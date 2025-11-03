"""
Scoring module for explainable hybrid resume-job matching.

This module provides:
- Deterministic scoring tools (skills, experience, education, salary, location)
- Semantic AI-powered scoring tools (soft skills, culture fit, growth potential)
- Bonus scoring tools (industry experience, rare skills, career trajectory)
- Score aggregation and explanation generation
"""

from .models import (
    ScoreBreakdown,
    DeterministicScore,
    SemanticScore,
    BonusScore,
    DetailedMatch
)

__all__ = [
    "ScoreBreakdown",
    "DeterministicScore",
    "SemanticScore",
    "BonusScore",
    "DetailedMatch"
]
