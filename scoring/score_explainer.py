"""
Score explainer for generating detailed match explanations.

This module generates comprehensive match reports including:
- Overall score and breakdown
- Strengths and weaknesses analysis
- Hiring recommendation
"""

import os
from typing import List, Tuple
from anthropic import Anthropic

from .models import (
    ScoreBreakdown,
    DeterministicScore,
    SemanticScore,
    BonusScore,
    DetailedMatch
)


class ScoreExplainer:
    """
    Generates detailed explanations for resume-job matches.

    This class takes the three scoring components (deterministic, semantic, bonus)
    and generates a comprehensive report with overall analysis, strengths,
    weaknesses, and hiring recommendation.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the score explainer.

        Args:
            api_key: Anthropic API key. If None, will use ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set or passed as argument")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"

    def generate_detailed_match(
        self,
        job_title: str,
        company: str,
        salary: int,
        location: str,
        deterministic_score: DeterministicScore,
        semantic_score: SemanticScore,
        bonus_score: BonusScore,
        resume_text: str = None,
        job_description: str = None
    ) -> DetailedMatch:
        """
        Generate a complete detailed match report.

        Args:
            job_title: Title of the job position
            company: Company name
            salary: Job salary
            location: Job location
            deterministic_score: Deterministic scoring results
            semantic_score: Semantic scoring results
            bonus_score: Bonus scoring results
            resume_text: Optional resume text for context
            job_description: Optional job description for context

        Returns:
            DetailedMatch object with complete match analysis
        """
        # Create score breakdown
        score_breakdown = ScoreBreakdown(
            deterministic=deterministic_score,
            semantic=semantic_score,
            bonus=bonus_score
        )

        total_score = score_breakdown.total_score

        # Generate AI-powered analysis
        overall_explanation = self._generate_overall_explanation(
            score_breakdown, job_title, resume_text, job_description
        )

        strengths = self._extract_strengths(score_breakdown)
        weaknesses = self._extract_weaknesses(score_breakdown)
        recommendation = self._generate_recommendation(total_score, strengths, weaknesses)

        return DetailedMatch(
            job_title=job_title,
            company=company,
            match_score=total_score,
            score_breakdown=score_breakdown,
            overall_explanation=overall_explanation,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation,
            salary=salary,
            location=location
        )

    def _generate_overall_explanation(
        self,
        score_breakdown: ScoreBreakdown,
        job_title: str,
        resume_text: str = None,
        job_description: str = None
    ) -> str:
        """
        Generate overall match explanation using AI.

        Args:
            score_breakdown: Complete score breakdown
            job_title: Job title
            resume_text: Optional resume text
            job_description: Optional job description

        Returns:
            Overall explanation text
        """
        total = score_breakdown.total_score
        det = score_breakdown.deterministic
        sem = score_breakdown.semantic
        bonus = score_breakdown.bonus

        # Create a summary of the scores for the prompt
        score_summary = f"""
TOTAL SCORE: {total:.1f}/100

BREAKDOWN:
1. Deterministic Score: {det.total:.1f}/40
   - Skills Matching: {det.skills_matching.score:.1f}/15
   - Experience Years: {det.experience_years.score:.1f}/10
   - Education Match: {det.education_match.score:.1f}/5
   - Salary Fit: {det.salary_fit.score:.1f}/5
   - Location Match: {det.location_match.score:.1f}/5

2. Semantic Score: {sem.total:.1f}/40
   - Soft Skills: {sem.soft_skills_match.score:.1f}/15
   - Culture Fit: {sem.culture_fit.score:.1f}/10
   - Growth Potential: {sem.growth_potential.score:.1f}/10
   - Project Relevance: {sem.project_relevance.score:.1f}/5

3. Bonus Score: {bonus.total:.1f}/20
   - Industry Experience: {bonus.industry_experience.score:.1f}/10
   - Rare Skills: {bonus.rare_skills_premium.score:.1f}/5
   - Career Trajectory: {bonus.career_trajectory.score:.1f}/5
"""

        prompt = f"""
Generate a concise overall explanation (2-3 sentences) for this resume-job match.

JOB TITLE: {job_title}

{score_summary}

Provide a concise summary that:
1. States the overall match quality (excellent/good/moderate/weak)
2. Highlights the top 2-3 strengths (highest scores)
3. Mentions 1-2 areas for improvement (lowest scores)

Keep it professional, factual, and actionable. Maximum 3 sentences.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Error generating explanation: {e}")
            # Fallback to template-based explanation
            return self._fallback_explanation(total, det, sem, bonus)

    def _fallback_explanation(
        self,
        total: float,
        det: DeterministicScore,
        sem: SemanticScore,
        bonus: BonusScore
    ) -> str:
        """Generate fallback explanation if AI fails."""
        quality = (
            "Excellent" if total >= 80 else
            "Good" if total >= 65 else
            "Moderate" if total >= 50 else
            "Weak"
        )

        # Find top strengths
        scores = [
            (det.skills_matching.score, "skills", 15),
            (det.experience_years.score, "experience", 10),
            (sem.soft_skills_match.score, "soft skills", 15),
            (sem.culture_fit.score, "culture fit", 10),
            (bonus.rare_skills_premium.score, "rare skills", 5),
        ]
        # Calculate percentage and sort
        percentages = [(s[0]/s[2], s[1]) for s in scores]
        percentages.sort(reverse=True)
        top_strengths = [s[1] for s in percentages[:2]]

        # Find weaknesses
        weaknesses = [s[1] for s in percentages[-2:]]

        return (
            f"{quality} candidate with {total:.0f}/100. "
            f"Strong {' and '.join(top_strengths)}. "
            f"Could improve {' and '.join(weaknesses)}."
        )

    def _extract_strengths(self, score_breakdown: ScoreBreakdown) -> List[str]:
        """
        Extract top strengths from score breakdown.

        Args:
            score_breakdown: Complete score breakdown

        Returns:
            List of strength descriptions
        """
        strengths = []

        det = score_breakdown.deterministic
        sem = score_breakdown.semantic
        bonus = score_breakdown.bonus

        # Check deterministic strengths
        if det.skills_matching.score >= 12:  # 80% of 15
            matched = len(det.skills_matching.metadata.get('matched_skills', []))
            strengths.append(f"Strong technical skills with {matched}+ matched competencies")

        if det.experience_years.score >= 8:  # 80% of 10
            years = det.experience_years.metadata.get('resume_years', 0)
            strengths.append(f"Excellent experience level ({years}+ years)")

        if det.education_match.score >= 4:  # 80% of 5
            strengths.append("Strong educational background")

        if det.salary_fit.score >= 4:  # 80% of 5
            strengths.append("Salary expectations well-aligned")

        if det.location_match.score >= 4:  # 80% of 5
            strengths.append("Excellent location fit")

        # Check semantic strengths
        if sem.soft_skills_match.score >= 12:  # 80% of 15
            strengths.append("Outstanding soft skills and communication")

        if sem.culture_fit.score >= 8:  # 80% of 10
            strengths.append("Excellent cultural alignment")

        if sem.growth_potential.score >= 8:  # 80% of 10
            strengths.append("High growth potential and adaptability")

        if sem.project_relevance.score >= 4:  # 80% of 5
            strengths.append("Highly relevant project experience")

        # Check bonus strengths
        if bonus.industry_experience.score >= 7:  # 70% of 10
            strengths.append("Strong industry-specific experience")

        if bonus.rare_skills_premium.score >= 4:  # 80% of 5
            strengths.append("Rare and highly valuable technical skills")

        if bonus.career_trajectory.score >= 4:  # 80% of 5
            strengths.append("Coherent and progressive career path")

        # If too many strengths, keep top ones
        if len(strengths) > 5:
            strengths = strengths[:5]

        return strengths if strengths else ["Meets basic requirements"]

    def _extract_weaknesses(self, score_breakdown: ScoreBreakdown) -> List[str]:
        """
        Extract main weaknesses from score breakdown.

        Args:
            score_breakdown: Complete score breakdown

        Returns:
            List of weakness descriptions
        """
        weaknesses = []

        det = score_breakdown.deterministic
        sem = score_breakdown.semantic
        bonus = score_breakdown.bonus

        # Check deterministic weaknesses
        if det.skills_matching.score < 10:  # Less than 67% of 15
            missing = len(det.skills_matching.metadata.get('missing_skills', []))
            if missing > 0:
                weaknesses.append(f"Missing {missing} key technical skills")

        if det.experience_years.score < 5:  # Less than 50% of 10
            req_years = det.experience_years.metadata.get('required_years', 0)
            weaknesses.append(f"Experience level below requirement ({req_years} years needed)")

        if det.education_match.score < 3:  # Less than 60% of 5
            weaknesses.append("Education level could be higher")

        if det.salary_fit.score < 3:  # Less than 60% of 5
            weaknesses.append("Salary expectations may not align")

        if det.location_match.score < 3:  # Less than 60% of 5
            weaknesses.append("Location not optimal")

        # Check semantic weaknesses
        if sem.soft_skills_match.score < 10:  # Less than 67% of 15
            weaknesses.append("Soft skills need development")

        if sem.culture_fit.score < 6:  # Less than 60% of 10
            weaknesses.append("Cultural fit uncertain")

        if sem.growth_potential.score < 6:  # Less than 60% of 10
            weaknesses.append("Growth potential unclear")

        if sem.project_relevance.score < 3:  # Less than 60% of 5
            weaknesses.append("Limited relevant project experience")

        # Check bonus weaknesses
        if bonus.industry_experience.score < 5:  # Less than 50% of 10
            weaknesses.append("Limited industry-specific experience")

        if bonus.rare_skills_premium.score < 2:  # Less than 40% of 5
            weaknesses.append("Few rare or specialized skills")

        if bonus.career_trajectory.score < 3:  # Less than 60% of 5
            weaknesses.append("Career progression unclear")

        # If too many weaknesses, keep most critical ones
        if len(weaknesses) > 4:
            weaknesses = weaknesses[:4]

        return weaknesses if weaknesses else ["No significant weaknesses identified"]

    def _generate_recommendation(
        self,
        total_score: float,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """
        Generate hiring recommendation based on score and analysis.

        Args:
            total_score: Total match score (0-100)
            strengths: List of strengths
            weaknesses: List of weaknesses

        Returns:
            Recommendation text
        """
        if total_score >= 85:
            return "Strongly recommended - Excellent candidate, proceed to interview immediately"
        elif total_score >= 75:
            return "Recommended - Strong candidate, proceed to interview"
        elif total_score >= 65:
            return "Consider for interview - Good candidate with minor gaps"
        elif total_score >= 50:
            return "Moderate fit - Review carefully before proceeding"
        else:
            return "Not recommended - Significant gaps in requirements"
