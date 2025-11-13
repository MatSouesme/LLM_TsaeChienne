"""
Profile Management Agent with LangChain ReAct Pattern.

This agent uses intelligent tools to analyze, optimize, and manage
candidate profiles for optimal job matching.

Features:
- Autonomous profile analysis
- Intelligent gap detection
- Proactive optimization suggestions
- Real-time match potential calculation
- Industry-specific recommendations
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate

from agents.profile_tools import ProfileToolkit
from storage.profiles_db import (
    save_profile, load_profile, delete_profile,
    save_conversation_message, load_conversation_history
)


class ProfileManagementAgent:
    """
    Intelligent agent for profile management using LangChain ReAct pattern.

    The agent can:
    - Analyze CV and extract structured data
    - Identify profile gaps and suggest improvements
    - Optimize profiles for specific industries
    - Calculate match potential with jobs
    - Validate profile consistency
    - Generate professional summaries
    """

    def __init__(
        self,
        api_key: str = None,
        job_database: List[Dict] = None,
        verbose: bool = True
    ):
        """
        Initialize the profile management agent.

        Args:
            api_key: Anthropic API key
            job_database: List of job offers for matching
            verbose: Print agent reasoning steps
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.job_database = job_database or []
        self.verbose = verbose

        # Initialize LLM (Haiku for cost efficiency)
        self.llm = ChatAnthropic(
            api_key=self.api_key,
            model="claude-3-haiku-20240307",
            temperature=0.7
        )

        # Initialize toolkit
        self.toolkit = ProfileToolkit(api_key=self.api_key, job_database=self.job_database)

        # Session storage (in-memory)
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Create a new profile management session or load from database.

        Args:
            session_id: Unique session identifier

        Returns:
            Session metadata
        """
        # Check in-memory cache first
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try loading from database
        db_data = load_profile(session_id)

        # Create memory for this session
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

        if db_data:
            # Restore from database
            session = {
                "session_id": session_id,
                "created_at": db_data["created_at"],
                "memory": memory,
                "profile": db_data["profile"],
                "state": db_data["state"],
                "tools_used": [],
                "completeness_score": db_data["completeness_score"]
            }

            # Restore conversation history to memory
            history = load_conversation_history(session_id)
            for msg in history:
                if msg["role"] == "user":
                    memory.chat_memory.add_user_message(msg["content"])
                else:
                    memory.chat_memory.add_ai_message(msg["content"])

            print(f"[ProfileAgent] Loaded session {session_id} from database (completeness: {db_data['completeness_score']}%)")
        else:
            # Create new session
            session = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "memory": memory,
                "profile": {},
                "state": "INITIAL",
                "tools_used": [],
                "completeness_score": 0
            }
            print(f"[ProfileAgent] Created new session {session_id}")

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get existing session from memory or database."""
        # Check in-memory first
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try loading from database
        return self.create_session(session_id) if load_profile(session_id) else None

    def reset_session(self, session_id: str):
        """Reset/clear a session from memory and database."""
        # Delete from memory
        if session_id in self.sessions:
            del self.sessions[session_id]

        # Delete from database
        delete_profile(session_id)
        print(f"[ProfileAgent] Deleted session {session_id}")

    def _create_tools(self, session_id: str) -> List[Tool]:
        """
        Create LangChain tools bound to a specific session.

        Args:
            session_id: Session to bind tools to

        Returns:
            List of LangChain Tool objects
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        profile = session["profile"]

        def extract_cv_data_wrapper(resume_text: str) -> str:
            """Extract structured data from CV."""
            session["tools_used"].append("extract_cv_structured_data")
            result = self.toolkit.extract_cv_structured_data(resume_text)
            # Update session profile
            try:
                extracted = json.loads(result)
                if "error" not in extracted:
                    session["profile"].update(extracted)
                    session["state"] = "ANALYZING"
            except:
                pass
            return result

        def update_profile_wrapper(field_value: str) -> str:
            """Update a profile field."""
            session["tools_used"].append("update_profile_field")
            result = self.toolkit.update_profile_field(profile, field_value)
            # Update completeness score
            try:
                result_data = json.loads(result)
                if "completeness" in result_data:
                    session["completeness_score"] = result_data["completeness"]
            except:
                pass
            return result

        def analyze_gaps_wrapper(dummy_input: str = "") -> str:
            """Analyze profile gaps."""
            session["tools_used"].append("analyze_profile_gaps")
            return self.toolkit.analyze_profile_gaps(profile)

        def suggest_skills_wrapper(target_industry: str = "") -> str:
            """Suggest complementary skills."""
            session["tools_used"].append("suggest_skill_additions")
            return self.toolkit.suggest_skill_additions(profile, target_industry or None)

        def validate_experience_wrapper(dummy_input: str = "") -> str:
            """Validate experience consistency."""
            session["tools_used"].append("validate_experience_consistency")
            return self.toolkit.validate_experience_consistency(profile)

        def calculate_matches_wrapper(dummy_input: str = "") -> str:
            """Calculate match potential."""
            session["tools_used"].append("calculate_match_potential")
            result = self.toolkit.calculate_match_potential(profile)
            session["state"] = "OPTIMIZING"
            return result

        def optimize_for_industry_wrapper(target_industry: str) -> str:
            """Optimize profile for specific industry."""
            session["tools_used"].append("optimize_profile_for_industry")
            return self.toolkit.optimize_profile_for_industry(profile, target_industry)

        def generate_summary_wrapper(dummy_input: str = "") -> str:
            """Generate professional summary."""
            session["tools_used"].append("generate_profile_summary")
            result = self.toolkit.generate_profile_summary(profile)
            session["state"] = "COMPLETE"
            return result

        tools = [
            Tool(
                name="extract_cv_structured_data",
                func=extract_cv_data_wrapper,
                description=(
                    "Extract structured profile data from a CV/resume text. "
                    "Input: full resume text. "
                    "Returns: JSON with skills, experience, education, location, etc. "
                    "Use this FIRST when user uploads a CV."
                )
            ),
            Tool(
                name="update_profile_field",
                func=update_profile_wrapper,
                description=(
                    "Update a specific field in the candidate profile. "
                    "Input: 'field|value' format (e.g., 'skills|Python,Docker' or 'salary|120000'). "
                    "Returns: confirmation with updated completeness score. "
                    "Use when user provides new information."
                )
            ),
            Tool(
                name="analyze_profile_gaps",
                func=analyze_gaps_wrapper,
                description=(
                    "Analyze the profile to identify missing information. "
                    "Input: empty string (uses current profile). "
                    "Returns: JSON with gaps, priorities, and completeness score. "
                    "Use to determine what to ask the user next."
                )
            ),
            Tool(
                name="suggest_skill_additions",
                func=suggest_skills_wrapper,
                description=(
                    "Suggest complementary skills for the candidate's target industry. "
                    "Input: target_industry (optional, uses profile industry if empty). "
                    "Returns: JSON with skill suggestions and justifications. "
                    "Use to help candidate improve their skill set."
                )
            ),
            Tool(
                name="validate_experience_consistency",
                func=validate_experience_wrapper,
                description=(
                    "Validate the consistency of experience timeline and progression. "
                    "Input: empty string (uses current profile). "
                    "Returns: JSON with validation results, warnings, and suggestions. "
                    "Use to check if experience data makes sense."
                )
            ),
            Tool(
                name="calculate_match_potential",
                func=calculate_matches_wrapper,
                description=(
                    "Calculate how many jobs match the current profile. "
                    "Input: empty string (uses current profile). "
                    "Returns: JSON with match count, top matches, and average score. "
                    "Use to show the candidate their current matching potential."
                )
            ),
            Tool(
                name="optimize_profile_for_industry",
                func=optimize_for_industry_wrapper,
                description=(
                    "Get industry-specific optimization recommendations. "
                    "Input: target_industry (e.g., 'fintech', 'tech', 'health'). "
                    "Returns: JSON with prioritized recommendations and impact estimates. "
                    "Use to provide strategic improvement suggestions."
                )
            ),
            Tool(
                name="generate_profile_summary",
                func=generate_summary_wrapper,
                description=(
                    "Generate a professional summary for the candidate. "
                    "Input: empty string (uses current profile). "
                    "Returns: JSON with polished professional summary text. "
                    "Use when profile is mostly complete to create a summary."
                )
            )
        ]

        return tools

    def _create_agent(self, session_id: str) -> AgentExecutor:
        """
        Create the LangChain ReAct agent for a session.

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

        # Define the agent prompt (simplified and strict)
        prompt = PromptTemplate.from_template("""
You are a Profile Optimization Assistant. Help candidates optimize their profiles for job matching.

RULES:
1. If user provides CV text: Use extract_cv_structured_data first
2. After extracting: Use analyze_profile_gaps to see what's missing
3. IMPORTANT: After analyzing gaps, ALWAYS use calculate_match_potential to show job matches
4. If gaps exist: Ask user ONE question about the most important gap
5. Keep responses SHORT and actionable
6. ALWAYS follow the format below EXACTLY

TOOLS:
{tools}

FORMAT (MUST FOLLOW EXACTLY):
Thought: [brief thought]
Action: [exact tool name from: {tool_names}]
Action Input: [input for tool]
Observation: [tool result appears here]
... (repeat if needed)
Thought: I have enough info to respond
Final Answer: [your response to user - be friendly and brief]

IMPORTANT:
- Use ONLY ONE Action per turn
- After Final Answer, STOP - don't add extra actions
- Keep Final Answer under 3 sentences
- Include numbers when available (completeness %, matches)

Previous messages:
{chat_history}

User: {input}

{agent_scratchpad}
""")

        # Create the ReAct agent
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
            max_iterations=8,  # Increased to 8 for better completion
            max_execution_time=30,  # Max 30 seconds
            handle_parsing_errors=True,
            early_stopping_method="generate",  # Return best answer when stopping
            return_intermediate_steps=self.verbose  # Return tool calls for transparency
        )

        return agent_executor

    def process_message(
        self,
        session_id: str,
        user_message: str,
        resume_text: str = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return agent response.

        Args:
            session_id: Session identifier
            user_message: User's message
            resume_text: Optional resume text (for CV upload)

        Returns:
            Response dict with agent reply, profile state, and tools used
        """
        # Get or create session
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        # If resume provided, save it IMMEDIATELY and prepend to message
        if resume_text:
            # Save resume_text directly to profile so it's available for advanced scoring
            session["profile"]["resume_text"] = resume_text
            print(f"[ProfileAgent] Saved resume_text ({len(resume_text)} chars) to profile")
            user_message = f"[CV UPLOADED]\n\n{resume_text}\n\nUser says: {user_message}"

        # Create agent
        agent_executor = self._create_agent(session_id)

        # Clear tools_used for this interaction
        session["tools_used"] = []

        try:
            # Run agent
            result = agent_executor.invoke({
                "input": user_message
            })

            # Extract tools used from intermediate steps if available
            tools_called = session["tools_used"]
            intermediate_steps = result.get("intermediate_steps", [])

            agent_response = result.get("output", "")

            # Save profile to database
            save_profile(
                session_id=session_id,
                profile_data=session["profile"],
                state=session["state"],
                completeness_score=session["completeness_score"]
            )

            # Save conversation messages to database
            save_conversation_message(session_id, "user", user_message)
            save_conversation_message(session_id, "agent", agent_response)

            response = {
                "session_id": session_id,
                "user_message": user_message,
                "agent_response": agent_response,
                "profile": session["profile"],
                "state": session["state"],
                "completeness_score": session["completeness_score"],
                "tools_used": tools_called,
                "intermediate_steps": len(intermediate_steps),
                "timestamp": datetime.now().isoformat()
            }

            print(f"[ProfileAgent] Saved session {session_id} to database")
            return response

        except Exception as e:
            return {
                "session_id": session_id,
                "user_message": user_message,
                "agent_response": f"I apologize, but I encountered an error: {str(e)}. Let me try a different approach.",
                "error": str(e),
                "profile": session["profile"],
                "completeness_score": session["completeness_score"],
                "timestamp": datetime.now().isoformat()
            }

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "state": session["state"],
            "profile": session["profile"],
            "completeness_score": session["completeness_score"],
            "message_count": len(session["memory"].chat_memory.messages),
            "tools_used_total": len(set(session.get("tools_used", [])))
        }

    def force_analyze_profile(self, session_id: str) -> Dict[str, Any]:
        """
        Force profile analysis without conversation.
        Useful for programmatic profile updates.
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        profile = session["profile"]

        # Run analysis tools
        gaps = json.loads(self.toolkit.analyze_profile_gaps(profile))
        matches = json.loads(self.toolkit.calculate_match_potential(profile))

        session["completeness_score"] = gaps.get("completeness_score", 0)

        return {
            "profile": profile,
            "gaps": gaps,
            "matches": matches,
            "completeness": gaps.get("completeness_score", 0)
        }
