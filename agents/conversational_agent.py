"""
Conversational Job Matching Agent with LangChain.

This agent uses ReAct pattern to:
1. Analyze candidate profile from resume
2. Ask clarifying questions when information is missing
3. Search for matching jobs intelligently
4. Present results with explanations

Features:
- Memory-enabled conversations (remembers context)
- Intelligent question generation
- Adaptive search strategy
- Integration with existing scoring system
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class ConversationalJobAgent:
    """
    Conversational agent for job matching with intelligent clarification.

    The agent:
    - Analyzes resume completeness
    - Asks ONE clarifying question at a time
    - Searches jobs when enough info is collected
    - Presents matches with reasoning
    """

    def __init__(
        self,
        api_key: str = None,
        job_database: List[Dict] = None,
        scoring_system = None,
        verbose: bool = True
    ):
        """
        Initialize the conversational agent.

        Args:
            api_key: Anthropic API key
            job_database: List of job offers to search from
            scoring_system: Reference to existing scoring system (optional)
            verbose: Print agent reasoning steps
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.job_database = job_database or []
        self.scoring_system = scoring_system
        self.verbose = verbose

        # Initialize advanced scoring system (lazy loading to avoid circular imports)
        self._advanced_scorer = None

        # Initialize LLM (using Haiku for cost efficiency + consistent with scoring system)
        self.llm = ChatAnthropic(
            api_key=self.api_key,
            model="claude-3-haiku-20240307",  # Fast, cheap, excellent for conversation + tool calling
            temperature=0.7
        )

        # Session storage (in-memory for now, can be Redis later)
        self.sessions: Dict[str, Dict[str, Any]] = {}

        # Initialize agent (done lazily per session)
        self._agent_executor = None

    def create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Create a new conversation session.

        Args:
            session_id: Unique session identifier

        Returns:
            Session metadata
        """
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Create memory for this session
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

        session = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "memory": memory,
            "candidate_profile": {},
            "state": "COLLECTING_INFO",  # COLLECTING_INFO, SEARCHING, PRESENTING
            "collected_info": {
                "resume_text": None,
                "industry": None,
                "location": None,
                "salary": None,
                "job_title_preference": None,
                "experience_level": None
            }
        }

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get existing session or None."""
        return self.sessions.get(session_id)

    def _create_tools(self, session_id: str) -> List[Tool]:
        """
        Create tools for the agent, bound to a specific session.

        Args:
            session_id: Session to bind tools to

        Returns:
            List of LangChain tools
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        def analyze_resume_completeness(resume_text: str) -> str:
            """
            Analyze what information is missing from the resume and candidate profile.
            Returns a JSON string with missing fields and suggestions.
            """
            collected = session["collected_info"]
            missing = []
            suggestions = []

            # Check what we already have
            if not collected["resume_text"]:
                collected["resume_text"] = resume_text

            # Analyze resume content
            resume_lower = resume_text.lower()

            # Check for salary expectation
            if not collected["salary"]:
                if "salary" not in resume_lower and "salaire" not in resume_lower:
                    missing.append("salary_expectation")
                    suggestions.append("What is your salary expectation?")

            # Check for location preference
            if not collected["location"]:
                if "location" not in resume_lower and "remote" not in resume_lower:
                    missing.append("location_preference")
                    suggestions.append("What is your preferred work location? (Remote, Paris, etc.)")

            # Check for industry preference
            if not collected["industry"]:
                missing.append("industry_preference")
                suggestions.append("What industry are you targeting? (fintech, health, tech, gambling, etc.)")

            # Check for job title preference
            if not collected["job_title_preference"]:
                missing.append("job_title_preference")
                suggestions.append("What type of role are you looking for?")

            # Extract experience level from resume
            if not collected["experience_level"]:
                years_match = re.search(r'(\d+)\+?\s*(?:years?|ans?)', resume_lower)
                if years_match:
                    years = int(years_match.group(1))
                    if years < 2:
                        collected["experience_level"] = "junior"
                    elif years < 5:
                        collected["experience_level"] = "mid"
                    else:
                        collected["experience_level"] = "senior"

            result = {
                "missing_fields": missing,
                "suggested_questions": suggestions,
                "completeness_score": (6 - len(missing)) / 6 * 100,
                "ready_to_search": len(missing) <= 2  # Can search with some missing info
            }

            return json.dumps(result, indent=2)

        def update_candidate_info(input_str: str) -> str:
            """
            Update candidate profile with new information.

            Args:
                input_str: String in format 'field|value' (e.g., 'salary|80000')

            Returns:
                Confirmation message
            """
            collected = session["collected_info"]

            # Parse input
            if '|' not in input_str:
                return "Error: Input must be in format 'field|value'"

            field, value = input_str.split('|', 1)
            field = field.lower().strip()
            value = value.strip()

            # Map field names
            field_mapping = {
                "salary": "salary",
                "salary_expectation": "salary",
                "location": "location",
                "location_preference": "location",
                "industry": "industry",
                "industry_preference": "industry",
                "job_title": "job_title_preference",
                "role": "job_title_preference"
            }

            if field in field_mapping:
                actual_field = field_mapping[field]
                collected[actual_field] = value
                return f"Updated {actual_field} to: {value}"

            return f"Unknown field: {field}"

        def search_matching_jobs(criteria: str = "") -> str:
            """
            Search for jobs matching candidate profile.

            Args:
                criteria: Optional additional search criteria (JSON string)

            Returns:
                JSON list of matching jobs with scores
            """
            collected = session["collected_info"]

            # Build search criteria
            industry = collected.get("industry")
            location = collected.get("location")
            salary = collected.get("salary")

            # Convert salary to int if provided
            min_salary = None
            if salary:
                try:
                    # Extract number from string (handle "80000", "80K", "€80,000")
                    salary_clean = re.sub(r'[^\d]', '', str(salary))
                    if salary_clean:
                        min_salary = int(salary_clean)
                        # Handle "80K" -> 80000
                        if min_salary < 1000:
                            min_salary *= 1000
                except ValueError:
                    pass

            # Filter jobs
            matched_jobs = []
            for job in self.job_database:
                # Industry filter
                if industry and job.get("industry", "").lower() != industry.lower():
                    continue

                # Salary filter
                if min_salary and job.get("salary", 0) < min_salary:
                    continue

                # Location filter (basic)
                if location:
                    job_location = job.get("location", "").lower()
                    location_lower = location.lower()
                    if "remote" not in location_lower and "remote" not in job_location:
                        if location_lower not in job_location:
                            continue

                matched_jobs.append(job)

            # Limit to top 20 for initial triage
            matched_jobs = matched_jobs[:20]

            # HYBRID SCORING APPROACH
            if collected["resume_text"]:
                # Step 1: Quick triage scoring (fast)
                quick_scored = []
                for job in matched_jobs:
                    quick_score = self._quick_score(collected["resume_text"], job)
                    if quick_score >= 45:  # Filter threshold
                        quick_scored.append((job, quick_score))

                # Sort by quick score
                quick_scored.sort(key=lambda x: x[1], reverse=True)
                top_candidates = quick_scored[:3]  # Top 3 for advanced scoring

                # Step 2: Advanced scoring for top candidates (detailed)
                final_scored = []
                for job, quick_score in top_candidates:
                    advanced_result = self._advanced_score(collected["resume_text"], job)

                    final_scored.append({
                        "title": job["title"],
                        "company": job["company"],
                        "location": job["location"],
                        "salary": job["salary"],
                        "industry": job.get("industry", ""),
                        "description": job.get("description", "")[:200],
                        "requirements": job.get("requirements", []),
                        "match_score": round(advanced_result['total'], 1),
                        "score_breakdown": {
                            "deterministic": round(advanced_result['deterministic'], 1),
                            "semantic": round(advanced_result['semantic'], 1),
                            "bonus": round(advanced_result['bonus'], 1)
                        },
                        "using_advanced_scoring": not advanced_result.get('using_fallback', False)
                    })

                matched_jobs = final_scored
            else:
                # No resume, return basic job list
                matched_jobs = [{
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "salary": job["salary"],
                    "industry": job.get("industry", ""),
                    "description": job.get("description", "")[:200]
                } for job in matched_jobs[:5]]

            if not matched_jobs:
                return json.dumps({
                    "count": 0,
                    "message": "No matching jobs found. Try broadening your criteria."
                })

            return json.dumps({
                "count": len(matched_jobs),
                "jobs": matched_jobs
            }, indent=2)

        def get_current_profile(unused_input: str = "") -> str:
            """
            Get current candidate profile summary.

            Args:
                unused_input: Ignored parameter (LangChain may pass empty string)

            Returns:
                JSON summary of collected information
            """
            collected = session["collected_info"]
            return json.dumps({
                "resume_provided": bool(collected["resume_text"]),
                "industry": collected.get("industry"),
                "location": collected.get("location"),
                "salary": collected.get("salary"),
                "job_title_preference": collected.get("job_title_preference"),
                "experience_level": collected.get("experience_level")
            }, indent=2)

        # Create tools list
        tools = [
            Tool(
                name="analyze_resume_completeness",
                func=analyze_resume_completeness,
                description=(
                    "Analyze a resume to determine what information is missing. "
                    "Input: resume text. "
                    "Returns: JSON with missing fields and suggested questions."
                )
            ),
            Tool(
                name="update_candidate_info",
                func=update_candidate_info,
                description=(
                    "Update candidate profile with new information from conversation. "
                    "Input: 'field|value' (e.g., 'salary|80000' or 'location|Paris'). "
                    "Returns: confirmation message."
                )
            ),
            Tool(
                name="search_matching_jobs",
                func=search_matching_jobs,
                description=(
                    "Search for jobs matching candidate profile. "
                    "Uses collected info (industry, location, salary). "
                    "Returns: JSON list of top matching jobs with scores."
                )
            ),
            Tool(
                name="get_current_profile",
                func=get_current_profile,
                description=(
                    "Get summary of currently collected candidate information. "
                    "No input required. "
                    "Returns: JSON summary."
                )
            )
        ]

        return tools

    def _get_advanced_scorer(self):
        """Lazy load the advanced scoring system."""
        if self._advanced_scorer is None:
            try:
                from scoring.scoring_agent import ScoringAgent
                self._advanced_scorer = ScoringAgent()
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Could not load advanced scorer: {e}")
                self._advanced_scorer = False  # Mark as unavailable
        return self._advanced_scorer if self._advanced_scorer else None

    def _quick_score(self, resume_text: str, job: Dict) -> float:
        """
        Quick scoring for job matching (simplified version for fast triage).

        Args:
            resume_text: Candidate resume
            job: Job description dict

        Returns:
            Match score (0-100)
        """
        resume_lower = resume_text.lower()
        score = 50.0  # Base score

        # Check requirements
        requirements = job.get("requirements", [])
        if requirements:
            matched = sum(1 for req in requirements if req.lower() in resume_lower)
            req_score = (matched / len(requirements)) * 30
            score += req_score

        # Check job description keywords
        job_desc = job.get("description", "").lower()
        common_words = set(job_desc.split()) & set(resume_lower.split())
        if common_words:
            desc_score = min(20, len(common_words) * 0.5)
            score += desc_score

        return min(100, score)

    def _advanced_score(self, resume_text: str, job: Dict) -> Dict:
        """
        Advanced scoring using the full scoring system (deterministic + semantic + bonus).

        Args:
            resume_text: Candidate resume
            job: Job description dict

        Returns:
            Dict with total score and breakdown
        """
        scorer = self._get_advanced_scorer()
        if not scorer:
            # Fallback to quick score if advanced scorer unavailable
            quick = self._quick_score(resume_text, job)
            return {
                'total': quick,
                'deterministic': quick * 0.4,
                'semantic': quick * 0.4,
                'bonus': quick * 0.2,
                'breakdown': {},
                'using_fallback': True
            }

        try:
            # Use the real ScoringAgent
            result = scorer.score_resume_job_match(
                resume_text=resume_text,
                job_description=job.get('description', ''),
                job_requirements=job.get('requirements', []),
                job_location=job.get('location', ''),
                job_salary=job.get('salary', 0),
                job_title=job.get('title', ''),
                industry=job.get('industry', '')
            )

            return {
                'total': result.total,
                'deterministic': result.deterministic_score,
                'semantic': result.semantic_score,
                'bonus': result.bonus_score,
                'breakdown': result.to_dict(),
                'using_fallback': False
            }
        except Exception as e:
            if self.verbose:
                print(f"Warning: Advanced scoring failed: {e}")
            # Fallback to quick score
            quick = self._quick_score(resume_text, job)
            return {
                'total': quick,
                'deterministic': quick * 0.4,
                'semantic': quick * 0.4,
                'bonus': quick * 0.2,
                'breakdown': {},
                'using_fallback': True
            }

    def _create_agent(self, session_id: str) -> AgentExecutor:
        """
        Create the LangChain agent for a session.

        Args:
            session_id: Session identifier

        Returns:
            Configured AgentExecutor
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        tools = self._create_tools(session_id)
        memory = session["memory"]

        # Define the agent prompt
        prompt = PromptTemplate.from_template("""
You are a friendly and intelligent job matching assistant. Your goal is to help candidates find the best job opportunities.

STRATEGY:
1. **Information Gathering**: When a candidate provides their resume or asks for help, analyze what information is missing
2. **Ask ONE Question at a Time**: If information is missing, ask the MOST IMPORTANT question first
3. **Search When Ready**: Once you have enough information (industry + resume at minimum), search for matching jobs
4. **Present Results**: Show top matches with clear reasoning

GUIDELINES:
- Be conversational and friendly
- Ask only ONE question per response (don't overwhelm the user)
- Prioritize critical info: industry > location > salary > job title
- When searching, use the search_matching_jobs tool
- Present results in a friendly, readable format (not raw JSON)
- If user asks to refine search, update info and search again

TOOLS AVAILABLE:
{tools}

TOOL NAMES: {tool_names}

Use this format:
Thought: [your reasoning about what to do next]
Action: [tool name from: {tool_names}]
Action Input: [input for the tool]
Observation: [result from tool]
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to respond
Final Answer: [your friendly response to the user]

IMPORTANT:
- Your "Final Answer" should be conversational, NOT raw JSON
- When presenting jobs, format them nicely
- Always explain WHY a job is a good match

Begin!

Chat History:
{chat_history}

User: {input}

{agent_scratchpad}
""")

        # Create the agent
        agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )

        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=self.verbose,
            max_iterations=15,  # Increased for complex multi-step searches
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )

        return agent_executor

    def chat(
        self,
        session_id: str,
        user_message: str,
        resume_text: str = None
    ) -> Dict[str, Any]:
        """
        Process a user message in a conversation.

        Args:
            session_id: Session identifier
            user_message: User's message
            resume_text: Optional resume text (for first message)

        Returns:
            Response dict with agent's reply and metadata
        """
        # Get or create session
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        # If resume provided, store it
        if resume_text:
            session["collected_info"]["resume_text"] = resume_text

        # Create agent for this session
        agent_executor = self._create_agent(session_id)

        try:
            # Run agent
            result = agent_executor.invoke({
                "input": user_message
            })

            response = {
                "session_id": session_id,
                "user_message": user_message,
                "agent_response": result.get("output", ""),
                "state": session["state"],
                "collected_info": session["collected_info"],
                "timestamp": datetime.now().isoformat()
            }

            return response

        except Exception as e:
            return {
                "session_id": session_id,
                "user_message": user_message,
                "agent_response": f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase your request?",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def reset_session(self, session_id: str):
        """Reset/clear a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session state."""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "state": session["state"],
            "collected_info": session["collected_info"],
            "message_count": len(session["memory"].chat_memory.messages)
        }
