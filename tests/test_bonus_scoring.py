"""
Test script for the bonus scoring tool.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.bonus_scoring_tool import BonusScoringTool
import json


def test_bonus_scoring():
    """Test the bonus scoring tool with a sample resume and job."""

    # Read test resume
    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()

    print("=" * 80)
    print("TEST: Bonus Scoring Tool")
    print("=" * 80)
    print(f"\nResume preview (first 300 chars):\n{resume_text[:300]}...")

    # Sample job data (from backend.py - Senior Python Developer in fintech)
    job_title = "Senior Python Developer"
    industry = "fintech"

    job_description = """
    We are looking for a Senior Python Developer to join our fintech team.
    You will build scalable backend systems and APIs for our financial platform.

    Requirements:
    - 5+ years of Python development experience
    - Strong experience with FastAPI or Django
    - Database design with PostgreSQL or MongoDB
    - Container technologies: Docker and Kubernetes
    - RESTful API design and microservices architecture
    - Test-driven development and CI/CD practices
    - Cloud platform experience (AWS, GCP, or Azure)
    - Experience in financial services or fintech is a plus
    - Knowledge of AI/ML for financial applications is valuable

    We offer competitive salary and remote work options.
    """

    # Initialize scoring tool
    print("\n" + "=" * 80)
    print("INITIALIZING BONUS SCORING TOOL...")
    print("=" * 80)

    try:
        scoring_tool = BonusScoringTool()
        print("[OK] Bonus scoring tool initialized")
    except ValueError as e:
        print(f"[ERROR] {e}")
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    # Calculate scores
    print("\n" + "=" * 80)
    print("CALCULATING BONUS SCORES (this may take ~20 seconds)...")
    print("=" * 80)

    score = scoring_tool.score_resume_job_match(
        resume_text=resume_text,
        job_description=job_description,
        job_title=job_title,
        industry=industry
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\n[SCORE] TOTAL BONUS SCORE: {score.total:.2f} / {score.max_total}")
    print(f"   Percentage: {(score.total / score.max_total * 100):.1f}%")

    print("\n" + "-" * 80)
    print("DETAILED BREAKDOWN:")
    print("-" * 80)

    print(f"\n1. Industry Experience: {score.industry_experience.score:.2f} / {score.industry_experience.max_score}")
    print(f"   {score.industry_experience.explanation}")

    print(f"\n2. Rare Skills Premium: {score.rare_skills_premium.score:.2f} / {score.rare_skills_premium.max_score}")
    print(f"   {score.rare_skills_premium.explanation}")

    print(f"\n3. Career Trajectory: {score.career_trajectory.score:.2f} / {score.career_trajectory.max_score}")
    print(f"   {score.career_trajectory.explanation}")

    # JSON output
    print("\n" + "=" * 80)
    print("JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(score.to_dict(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("[OK] TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    test_bonus_scoring()
