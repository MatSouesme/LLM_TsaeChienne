"""
Bonus scoring tool for advanced candidate evaluation.

This tool uses AI to analyze:
- Industry Experience (10 points): Domain-specific expertise
- Rare Skills Premium (5 points): Rare and highly sought-after skills
- Career Trajectory (5 points): Career progression and coherence
"""

import os
from typing import Dict, Any
from anthropic import Anthropic

from .models import BonusScore, ScoreDetail


class BonusScoringTool:
    """
    Tool for bonus scoring using Claude API.

    This tool analyzes advanced aspects that can differentiate top candidates:
    - Industry-specific experience and domain knowledge
    - Rare and valuable technical skills
    - Career coherence and progression
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the bonus scoring tool.

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
        industry: str = None
    ) -> BonusScore:
        """
        Calculate bonus scores for a resume-job match.

        Args:
            resume_text: Full text of the candidate's resume
            job_description: Full job description
            job_title: Title of the job position
            industry: Optional specific industry (e.g., "fintech", "healthcare")

        Returns:
            BonusScore object with all bonus scoring components
        """
        # Score each component
        industry_exp = self._score_industry_experience(resume_text, job_description, industry)
        rare_skills = self._score_rare_skills(resume_text, job_description, job_title)
        career_trajectory = self._score_career_trajectory(resume_text, job_title)

        return BonusScore(
            industry_experience=industry_exp,
            rare_skills_premium=rare_skills,
            career_trajectory=career_trajectory
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

    def _score_industry_experience(
        self,
        resume_text: str,
        job_description: str,
        industry: str = None
    ) -> ScoreDetail:
        """
        Score industry experience (10 points max).

        Analyzes domain-specific expertise and knowledge.
        """
        industry_context = f"\nINDUSTRY: {industry}" if industry else ""

        prompt = f"""
Analyze the candidate's industry-specific experience for this job.

JOB DESCRIPTION:
{job_description}{industry_context}

CANDIDATE RESUME:
{resume_text}

Evaluate the candidate's industry experience based on:
1. Years in the specific industry: How long has the candidate worked in this industry?
2. Domain knowledge: Does the candidate understand industry-specific challenges?
3. Relevant projects: Has the candidate worked on industry-relevant projects?
4. Industry-specific skills: Does the candidate have specialized domain skills?

Scoring guidelines:
- 10 points: 5+ years in the exact industry with deep domain expertise
- 7-9 points: 3-5 years in the industry or related fields
- 4-6 points: 1-3 years or transferable experience from adjacent industries
- 1-3 points: No direct industry experience but relevant skills
- 0 points: No relevant industry experience

Provide:
1. A score from 0 to 10
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

    def _score_rare_skills(
        self,
        resume_text: str,
        job_description: str,
        job_title: str
    ) -> ScoreDetail:
        """
        Score rare skills premium (5 points max).

        Analyzes rare, highly valuable, and hard-to-find technical skills that are RELEVANT to the job.
        """
        prompt = f"""
Analyze the candidate's rare and highly sought-after skills FOR THIS SPECIFIC JOB.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

CRITICAL INSTRUCTION: Only award points for rare skills that are RELEVANT and VALUABLE for this specific job position.
Rare skills that are irrelevant to the job should score 0 points.

For example:
- AI/ML skills are rare and valuable for a Data Scientist job (high score)
- AI/ML skills are irrelevant for a Truck Driver job (0 points)
- CDL license + hazmat certification are rare for a Truck Driver (high score)
- CDL license is irrelevant for a Data Scientist (0 points)

Evaluate rare skills based on:
1. Relevance FIRST: Is this skill valuable for THIS job?
2. Rarity: Is this skill hard to find in candidates for this position?
3. Market demand: Is this skill in high demand for this role?
4. Competitive advantage: Does this skill differentiate the candidate?

Scoring guidelines:
- 5 points: Multiple rare skills that are extremely hard to find AND highly relevant
- 4 points: At least one rare skill in high demand AND relevant to the job
- 3 points: Some specialized skills that add value to this position
- 1-2 points: Minor differentiating skills
- 0 points: No rare skills OR skills are irrelevant to this job

Provide:
1. A score from 0 to 5
2. A concise explanation (1-2 sentences) listing the rare skills and their relevance

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

    def _score_career_trajectory(
        self,
        resume_text: str,
        job_title: str
    ) -> ScoreDetail:
        """
        Score career trajectory (5 points max).

        Analyzes career coherence, progression, and logical advancement.
        """
        prompt = f"""
Analyze the candidate's career trajectory and progression.

JOB TITLE: {job_title}

CANDIDATE RESUME:
{resume_text}

Evaluate career trajectory based on:
1. Coherence: Is there a logical progression and story?
2. Advancement: Has the candidate taken on increasing responsibilities?
3. Consistency: No unexplained gaps or frequent job-hopping?
4. Fit: Is this next position a natural next step?

Scoring guidelines:
- 5 points: Clear, coherent progression with steady advancement
- 4 points: Good progression with minor gaps or pivots
- 3 points: Acceptable trajectory with some inconsistencies
- 1-2 points: Fragmented career or unclear direction
- 0 points: Incoherent trajectory or major red flags

Provide:
1. A score from 0 to 5
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
                    # Extract just the number (handle formats like "8.5/10" or "8.5")
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
