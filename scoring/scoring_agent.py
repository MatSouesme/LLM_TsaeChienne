"""
Scoring agent that orchestrates all scoring components.

This agent coordinates:
1. Deterministic scoring (40 points)
2. Semantic scoring (40 points)
3. Bonus scoring (20 points)
4. Score explanation and report generation

Total: 100 points with detailed breakdown and justifications.
"""

import os
from typing import List, Dict, Any

from .deterministic_scoring_tool import DeterministicScoringTool
from .semantic_scoring_tool import SemanticScoringTool
from .bonus_scoring_tool import BonusScoringTool
from .score_explainer import ScoreExplainer
from .models import DetailedMatch


class ScoringAgent:
    """
    Main scoring agent that orchestrates all scoring components.

    This agent provides a single interface to:
    - Calculate deterministic scores (skills, experience, education, salary, location)
    - Calculate semantic scores (soft skills, culture fit, growth potential, projects)
    - Calculate bonus scores (industry experience, rare skills, career trajectory)
    - Generate detailed explanations and recommendations
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the scoring agent with all tools.

        Args:
            api_key: Anthropic API key. If None, will use ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set or passed as argument")

        # Initialize all scoring tools
        self.deterministic_tool = DeterministicScoringTool()
        self.semantic_tool = SemanticScoringTool(api_key=self.api_key)
        self.bonus_tool = BonusScoringTool(api_key=self.api_key)
        self.explainer = ScoreExplainer(api_key=self.api_key)

    def score_candidate(
        self,
        resume_text: str,
        job_title: str,
        company: str,
        job_description: str,
        job_requirements: List[str],
        job_location: str,
        job_salary: int,
        candidate_location: str = None,
        candidate_salary_expectation: int = None,
        industry: str = None,
        company_culture: str = None
    ) -> DetailedMatch:
        """
        Score a candidate for a job position.

        This method calculates all scores and generates a complete match report.

        Args:
            resume_text: Full text of the candidate's resume
            job_title: Title of the job position
            company: Company name
            job_description: Full job description
            job_requirements: List of specific job requirements
            job_location: Job location
            job_salary: Job salary
            candidate_location: Optional candidate location
            candidate_salary_expectation: Optional candidate salary expectation
            industry: Optional industry (e.g., "fintech", "healthcare")
            company_culture: Optional company culture description

        Returns:
            DetailedMatch object with complete scoring and analysis
        """
        print("Starting scoring process...")

        # Step 1: Deterministic Scoring (40 points)
        print("  [1/4] Calculating deterministic scores...")
        deterministic_score = self.deterministic_tool.score_resume_job_match(
            resume_text=resume_text,
            job_requirements=job_requirements,
            job_description=job_description,
            job_location=job_location,
            job_salary=job_salary,
            candidate_location=candidate_location,
            candidate_salary_expectation=candidate_salary_expectation,
            job_title=job_title
        )
        print(f"        Deterministic: {deterministic_score.total:.1f}/40")

        # Step 2: Semantic Scoring (40 points)
        print("  [2/4] Calculating semantic scores (AI analysis, ~30s)...")
        semantic_score = self.semantic_tool.score_resume_job_match(
            resume_text=resume_text,
            job_description=job_description,
            job_title=job_title,
            company_culture=company_culture
        )
        print(f"        Semantic: {semantic_score.total:.1f}/40")

        # Step 3: Bonus Scoring (20 points)
        print("  [3/4] Calculating bonus scores (AI analysis, ~20s)...")
        bonus_score = self.bonus_tool.score_resume_job_match(
            resume_text=resume_text,
            job_description=job_description,
            job_title=job_title,
            industry=industry
        )
        print(f"        Bonus: {bonus_score.total:.1f}/20")

        # Step 4: Generate Explanation and Report
        print("  [4/4] Generating detailed match report...")
        detailed_match = self.explainer.generate_detailed_match(
            job_title=job_title,
            company=company,
            salary=job_salary,
            location=job_location,
            deterministic_score=deterministic_score,
            semantic_score=semantic_score,
            bonus_score=bonus_score,
            resume_text=resume_text,
            job_description=job_description
        )

        print(f"\n[COMPLETE] Total Score: {detailed_match.match_score:.1f}/100")
        print(f"           Recommendation: {detailed_match.recommendation}")

        return detailed_match

    def score_candidate_simple(
        self,
        resume_text: str,
        job_data: Dict[str, Any]
    ) -> DetailedMatch:
        """
        Simplified interface that accepts job data as a dictionary.

        This is a convenience method for easier integration with existing code.

        Args:
            resume_text: Full text of the candidate's resume
            job_data: Dictionary with job information containing:
                - title: Job title
                - company: Company name
                - description: Job description
                - requirements: List of requirements
                - location: Job location
                - salary: Job salary
                - industry: Optional industry
                - culture: Optional company culture

        Returns:
            DetailedMatch object with complete scoring and analysis
        """
        return self.score_candidate(
            resume_text=resume_text,
            job_title=job_data.get("title", ""),
            company=job_data.get("company", ""),
            job_description=job_data.get("description", ""),
            job_requirements=job_data.get("requirements", []),
            job_location=job_data.get("location", ""),
            job_salary=job_data.get("salary", 0),
            candidate_location=job_data.get("candidate_location"),
            candidate_salary_expectation=job_data.get("candidate_salary"),
            industry=job_data.get("industry"),
            company_culture=job_data.get("culture")
        )

    def get_score_breakdown_dict(self, detailed_match: DetailedMatch) -> Dict[str, Any]:
        """
        Convert DetailedMatch to a dictionary format.

        Args:
            detailed_match: DetailedMatch object

        Returns:
            Dictionary representation of the match
        """
        return detailed_match.to_dict()
