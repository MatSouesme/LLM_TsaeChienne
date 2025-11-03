"""
Test script for the semantic scoring tool.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.semantic_scoring_tool import SemanticScoringTool
import json


def test_semantic_scoring():
    """Test the semantic scoring tool with a sample resume and job."""

    # Read test resume
    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()

    print("=" * 80)
    print("TEST: Semantic Scoring Tool")
    print("=" * 80)
    print(f"\nResume preview (first 300 chars):\n{resume_text[:300]}...")

    # Sample job data (from backend.py - Senior Python Developer)
    job_title = "Senior Python Developer"

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

    We value:
    - Strong communication skills and teamwork
    - Problem-solving mindset
    - Initiative and ownership
    - Continuous learning
    - Collaborative work environment

    We offer competitive salary and remote work options.
    """

    company_culture = """
    We are a fast-growing fintech startup with a focus on innovation and excellence.
    Our culture values:
    - Collaboration and open communication
    - Taking ownership and initiative
    - Continuous learning and growth
    - Work-life balance with remote-first approach
    - Diversity and inclusion
    """

    # Initialize scoring tool
    print("\n" + "=" * 80)
    print("INITIALIZING SEMANTIC SCORING TOOL...")
    print("=" * 80)

    try:
        scoring_tool = SemanticScoringTool()
        print("[OK] Semantic scoring tool initialized")
    except ValueError as e:
        print(f"[ERROR] {e}")
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    # Calculate scores
    print("\n" + "=" * 80)
    print("CALCULATING SEMANTIC SCORES (this may take ~30 seconds)...")
    print("=" * 80)

    score = scoring_tool.score_resume_job_match(
        resume_text=resume_text,
        job_description=job_description,
        job_title=job_title,
        company_culture=company_culture
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\n[SCORE] TOTAL SEMANTIC SCORE: {score.total:.2f} / {score.max_total}")
    print(f"   Percentage: {(score.total / score.max_total * 100):.1f}%")

    print("\n" + "-" * 80)
    print("DETAILED BREAKDOWN:")
    print("-" * 80)

    print(f"\n1. Soft Skills Match: {score.soft_skills_match.score:.2f} / {score.soft_skills_match.max_score}")
    print(f"   {score.soft_skills_match.explanation}")

    print(f"\n2. Culture Fit: {score.culture_fit.score:.2f} / {score.culture_fit.max_score}")
    print(f"   {score.culture_fit.explanation}")

    print(f"\n3. Growth Potential: {score.growth_potential.score:.2f} / {score.growth_potential.max_score}")
    print(f"   {score.growth_potential.explanation}")

    print(f"\n4. Project Relevance: {score.project_relevance.score:.2f} / {score.project_relevance.max_score}")
    print(f"   {score.project_relevance.explanation}")

    # JSON output
    print("\n" + "=" * 80)
    print("JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(score.to_dict(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("[OK] TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    test_semantic_scoring()
