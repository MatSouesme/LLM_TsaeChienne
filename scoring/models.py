"""
Data models for the scoring system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ScoreDetail:
    """Individual score component with explanation."""
    score: float
    max_score: float
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeterministicScore:
    """Deterministic scoring results (40 points max)."""
    skills_matching: ScoreDetail
    experience_years: ScoreDetail
    education_match: ScoreDetail
    salary_fit: ScoreDetail
    location_match: ScoreDetail

    @property
    def total(self) -> float:
        return (
            self.skills_matching.score +
            self.experience_years.score +
            self.education_match.score +
            self.salary_fit.score +
            self.location_match.score
        )

    @property
    def max_total(self) -> float:
        return 40.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": round(self.total, 2),
            "max": self.max_total,
            "details": {
                "skills_matching": {
                    "score": round(self.skills_matching.score, 2),
                    "max": self.skills_matching.max_score,
                    "explanation": self.skills_matching.explanation,
                    **self.skills_matching.metadata
                },
                "experience_years": {
                    "score": round(self.experience_years.score, 2),
                    "max": self.experience_years.max_score,
                    "explanation": self.experience_years.explanation,
                    **self.experience_years.metadata
                },
                "education_match": {
                    "score": round(self.education_match.score, 2),
                    "max": self.education_match.max_score,
                    "explanation": self.education_match.explanation,
                    **self.education_match.metadata
                },
                "salary_fit": {
                    "score": round(self.salary_fit.score, 2),
                    "max": self.salary_fit.max_score,
                    "explanation": self.salary_fit.explanation,
                    **self.salary_fit.metadata
                },
                "location_match": {
                    "score": round(self.location_match.score, 2),
                    "max": self.location_match.max_score,
                    "explanation": self.location_match.explanation,
                    **self.location_match.metadata
                }
            }
        }


@dataclass
class SemanticScore:
    """Semantic AI-powered scoring results (40 points max)."""
    soft_skills_match: ScoreDetail
    culture_fit: ScoreDetail
    growth_potential: ScoreDetail
    project_relevance: ScoreDetail

    @property
    def total(self) -> float:
        return (
            self.soft_skills_match.score +
            self.culture_fit.score +
            self.growth_potential.score +
            self.project_relevance.score
        )

    @property
    def max_total(self) -> float:
        return 40.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": round(self.total, 2),
            "max": self.max_total,
            "details": {
                "soft_skills_match": {
                    "score": round(self.soft_skills_match.score, 2),
                    "max": self.soft_skills_match.max_score,
                    "explanation": self.soft_skills_match.explanation
                },
                "culture_fit": {
                    "score": round(self.culture_fit.score, 2),
                    "max": self.culture_fit.max_score,
                    "explanation": self.culture_fit.explanation
                },
                "growth_potential": {
                    "score": round(self.growth_potential.score, 2),
                    "max": self.growth_potential.max_score,
                    "explanation": self.growth_potential.explanation
                },
                "project_relevance": {
                    "score": round(self.project_relevance.score, 2),
                    "max": self.project_relevance.max_score,
                    "explanation": self.project_relevance.explanation
                }
            }
        }


@dataclass
class BonusScore:
    """Bonus scoring results (20 points max)."""
    industry_experience: ScoreDetail
    rare_skills_premium: ScoreDetail
    career_trajectory: ScoreDetail

    @property
    def total(self) -> float:
        return (
            self.industry_experience.score +
            self.rare_skills_premium.score +
            self.career_trajectory.score
        )

    @property
    def max_total(self) -> float:
        return 20.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": round(self.total, 2),
            "max": self.max_total,
            "details": {
                "industry_experience": {
                    "score": round(self.industry_experience.score, 2),
                    "max": self.industry_experience.max_score,
                    "explanation": self.industry_experience.explanation
                },
                "rare_skills_premium": {
                    "score": round(self.rare_skills_premium.score, 2),
                    "max": self.rare_skills_premium.max_score,
                    "explanation": self.rare_skills_premium.explanation
                },
                "career_trajectory": {
                    "score": round(self.career_trajectory.score, 2),
                    "max": self.career_trajectory.max_score,
                    "explanation": self.career_trajectory.explanation
                }
            }
        }


@dataclass
class ScoreBreakdown:
    """Complete score breakdown for a resume-job match."""
    deterministic: DeterministicScore
    semantic: SemanticScore
    bonus: BonusScore

    @property
    def total_score(self) -> float:
        return self.deterministic.total + self.semantic.total + self.bonus.total

    @property
    def max_score(self) -> float:
        return 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deterministic": self.deterministic.to_dict(),
            "semantic": self.semantic.to_dict(),
            "bonus": self.bonus.to_dict()
        }


@dataclass
class DetailedMatch:
    """Complete match result with score breakdown and explanations."""
    job_title: str
    company: str
    match_score: float
    score_breakdown: ScoreBreakdown
    overall_explanation: str
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    salary: int
    location: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_title": self.job_title,
            "company": self.company,
            "match_score": round(self.match_score, 2),
            "score_breakdown": self.score_breakdown.to_dict(),
            "overall_explanation": self.overall_explanation,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendation": self.recommendation,
            "salary": self.salary,
            "location": self.location
        }
