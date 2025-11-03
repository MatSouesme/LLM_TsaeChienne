"""
Semantic scoring tool using AI for soft skills, culture fit, and qualitative analysis.

This tool uses Claude to analyze:
- Soft Skills Match (15 points): Leadership, communication, teamwork, problem-solving
- Culture Fit (10 points): Values alignment, work style compatibility
- Growth Potential (10 points): Learning capacity, career progression, adaptability
- Project Relevance (5 points): Similarity of past projects to the job requirements
"""

import os
from typing import Dict, Any
from anthropic import Anthropic

from .models import SemanticScore, ScoreDetail


class SemanticScoringTool:
    """
    Tool for semantic scoring using Claude API.

    This tool analyzes qualitative aspects of a resume-job match that require
    natural language understanding and contextual reasoning.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the semantic scoring tool.

        Args:
            api_key: Anthropic API key. If None, will use ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set or passed as argument")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"

    def score_resume_job_match(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company_culture: str = None
    ) -> SemanticScore:
        """
        Calculate semantic scores for a resume-job match.

        Args:
            resume_text: Full text of the candidate's resume
            job_description: Full job description
            job_title: Title of the job position
            company_culture: Optional description of company culture/values

        Returns:
            SemanticScore object with all semantic scoring components
        """
        # Score each component
        soft_skills = self._score_soft_skills(resume_text, job_description, job_title)
        culture_fit = self._score_culture_fit(resume_text, job_description, company_culture)
        growth_potential = self._score_growth_potential(resume_text, job_title)
        project_relevance = self._score_project_relevance(resume_text, job_description)

        return SemanticScore(
            soft_skills_match=soft_skills,
            culture_fit=culture_fit,
            growth_potential=growth_potential,
            project_relevance=project_relevance
        )

    def _call_claude(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Call Claude API with a prompt.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in the response

        Returns:
            Claude's response text
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            raise

    def _score_soft_skills(
        self,
        resume_text: str,
        job_description: str,
        job_title: str
    ) -> ScoreDetail:
        """
        Score soft skills match (15 points max).

        Analyzes: Leadership, communication, teamwork, problem-solving, initiative.
        """
        prompt = f"""
Analyze the soft skills match between this resume and job position.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

Evaluate the candidate's soft skills based on:
1. Leadership: Ability to lead projects, teams, or initiatives
2. Communication: Written and verbal communication skills
3. Teamwork: Collaboration and working with others
4. Problem-solving: Analytical thinking and solution-oriented approach
5. Initiative: Proactiveness and self-motivation

Provide:
1. A score from 0 to 15 (15 = exceptional soft skills match)
2. A concise explanation (2-3 sentences) justifying the score

Format your response EXACTLY as:
SCORE: [number]
EXPLANATION: [your explanation]
"""

        response = self._call_claude(prompt)
        score, explanation = self._parse_score_response(response, max_score=15.0)

        return ScoreDetail(
            score=score,
            max_score=15.0,
            explanation=explanation
        )

    def _score_culture_fit(
        self,
        resume_text: str,
        job_description: str,
        company_culture: str = None
    ) -> ScoreDetail:
        """
        Score culture fit (10 points max).

        Analyzes values alignment and work style compatibility.
        """
        culture_context = f"\nCOMPANY CULTURE:\n{company_culture}" if company_culture else ""

        prompt = f"""
Analyze the culture fit between this candidate and the company/role.

JOB DESCRIPTION:
{job_description}{culture_context}

CANDIDATE RESUME:
{resume_text}

Evaluate the candidate's culture fit based on:
1. Values alignment: Do the candidate's values match the company's?
2. Work style: Does the candidate's approach match the role expectations?
3. Environment preference: Does the candidate thrive in this type of environment?
4. Long-term fit: Is this a mutually beneficial match?

Provide:
1. A score from 0 to 10 (10 = perfect culture fit)
2. A concise explanation (2-3 sentences) justifying the score

Format your response EXACTLY as:
SCORE: [number]
EXPLANATION: [your explanation]
"""

        response = self._call_claude(prompt)
        score, explanation = self._parse_score_response(response, max_score=10.0)

        return ScoreDetail(
            score=score,
            max_score=10.0,
            explanation=explanation
        )

    def _score_growth_potential(
        self,
        resume_text: str,
        job_title: str
    ) -> ScoreDetail:
        """
        Score growth potential (10 points max).

        Analyzes learning capacity, career progression, and adaptability.
        """
        prompt = f"""
Analyze the candidate's growth potential for this role.

JOB TITLE: {job_title}

CANDIDATE RESUME:
{resume_text}

Evaluate the candidate's growth potential based on:
1. Learning capacity: Evidence of continuous learning, certifications, new skills
2. Career progression: Trajectory showing increasing responsibilities
3. Adaptability: Ability to adapt to new technologies, roles, or environments
4. Future potential: Likelihood of excelling and growing in this role

Provide:
1. A score from 0 to 10 (10 = exceptional growth potential)
2. A concise explanation (2-3 sentences) justifying the score

Format your response EXACTLY as:
SCORE: [number]
EXPLANATION: [your explanation]
"""

        response = self._call_claude(prompt)
        score, explanation = self._parse_score_response(response, max_score=10.0)

        return ScoreDetail(
            score=score,
            max_score=10.0,
            explanation=explanation
        )

    def _score_project_relevance(
        self,
        resume_text: str,
        job_description: str
    ) -> ScoreDetail:
        """
        Score project relevance (5 points max).

        Analyzes similarity of past projects to job requirements.
        """
        prompt = f"""
Analyze the relevance of the candidate's past projects to this job.

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

Evaluate project relevance based on:
1. Domain similarity: Are the projects in a similar domain/industry?
2. Technical similarity: Do the projects use similar technologies?
3. Scope similarity: Are the project scopes comparable?
4. Impact: Did the projects have measurable, relevant impact?

Provide:
1. A score from 0 to 5 (5 = highly relevant projects)
2. A concise explanation (1-2 sentences) justifying the score

Format your response EXACTLY as:
SCORE: [number]
EXPLANATION: [your explanation]
"""

        response = self._call_claude(prompt)
        score, explanation = self._parse_score_response(response, max_score=5.0)

        return ScoreDetail(
            score=score,
            max_score=5.0,
            explanation=explanation
        )

    def _parse_score_response(self, response: str, max_score: float) -> tuple[float, str]:
        """
        Parse Claude's response to extract score and explanation.

        Expected format:
        SCORE: [number]
        EXPLANATION: [text]

        Args:
            response: Raw response from Claude
            max_score: Maximum allowed score

        Returns:
            Tuple of (score, explanation)
        """
        try:
            lines = response.strip().split('\n')
            score = None
            explanation = None

            for line in lines:
                if line.startswith('SCORE:'):
                    score_text = line.replace('SCORE:', '').strip()
                    # Extract just the number (handle formats like "12.5/15" or "12.5")
                    score_text = score_text.split('/')[0].strip()
                    score = float(score_text)
                elif line.startswith('EXPLANATION:'):
                    explanation = line.replace('EXPLANATION:', '').strip()

            # Validate score
            if score is None:
                # Fallback: try to find any number in the response
                import re
                numbers = re.findall(r'\d+\.?\d*', response)
                if numbers:
                    score = float(numbers[0])
                else:
                    score = 0.0
                    print(f"Warning: Could not parse score from response: {response[:100]}")

            # Clamp score to valid range
            score = max(0.0, min(score, max_score))

            # Get explanation
            if not explanation:
                # Use the whole response as explanation if not explicitly formatted
                explanation = response.strip()

            return score, explanation

        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response was: {response[:200]}")
            return 0.0, f"Error parsing response: {str(e)}"
