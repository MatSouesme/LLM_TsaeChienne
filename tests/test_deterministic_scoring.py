"""
Test script for the deterministic scoring tool.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.deterministic_scoring_tool import DeterministicScoringTool
import json


def test_deterministic_scoring():
    """Test the deterministic scoring tool with a sample resume and job."""

    # Read test resume
    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()

    print("=" * 80)
    print("TEST: Deterministic Scoring Tool")
    print("=" * 80)
    print(f"\nResume preview (first 300 chars):\n{resume_text[:300]}...")

    # Sample job data (from backend.py - Senior Python Developer)
    job_requirements = [
        "5+ years Python experience",
        "FastAPI or Django expertise",
        "PostgreSQL/MongoDB knowledge",
        "Docker and Kubernetes",
        "RESTful APIs design",
        "Test-driven development",
        "Cloud platforms (AWS, GCP, or Azure)",
        "CI/CD pipelines"
    ]

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

    We offer competitive salary and remote work options.
    """

    job_location = "Paris / Remote"
    job_salary = 130000
    candidate_location = "Paris"
    candidate_salary = 120000

    # Initialize scoring tool
    scoring_tool = DeterministicScoringTool()

    # Calculate scores
    print("\n" + "=" * 80)
    print("CALCULATING DETERMINISTIC SCORES...")
    print("=" * 80)

    score = scoring_tool.score_resume_job_match(
        resume_text=resume_text,
        job_requirements=job_requirements,
        job_description=job_description,
        job_location=job_location,
        job_salary=job_salary,
        candidate_location=candidate_location,
        candidate_salary_expectation=candidate_salary
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\n[SCORE] TOTAL DETERMINISTIC SCORE: {score.total:.2f} / {score.max_total}")
    print(f"   Percentage: {(score.total / score.max_total * 100):.1f}%")

    print("\n" + "-" * 80)
    print("DETAILED BREAKDOWN:")
    print("-" * 80)

    print(f"\n1. Skills Matching: {score.skills_matching.score:.2f} / {score.skills_matching.max_score}")
    print(f"   {score.skills_matching.explanation}")
    print(f"   Matched: {score.skills_matching.metadata.get('matched_skills', [])}")
    print(f"   Missing: {score.skills_matching.metadata.get('missing_skills', [])}")

    print(f"\n2. Experience Years: {score.experience_years.score:.2f} / {score.experience_years.max_score}")
    print(f"   {score.experience_years.explanation}")
    print(f"   Resume: {score.experience_years.metadata.get('resume_years')} years")
    print(f"   Required: {score.experience_years.metadata.get('required_years')} years")

    print(f"\n3. Education Match: {score.education_match.score:.2f} / {score.education_match.max_score}")
    print(f"   {score.education_match.explanation}")

    print(f"\n4. Salary Fit: {score.salary_fit.score:.2f} / {score.salary_fit.max_score}")
    print(f"   {score.salary_fit.explanation}")
    print(f"   Job: €{score.salary_fit.metadata.get('job_salary'):,}")
    if score.salary_fit.metadata.get('candidate_expectation'):
        print(f"   Expected: €{score.salary_fit.metadata.get('candidate_expectation'):,}")

    print(f"\n5. Location Match: {score.location_match.score:.2f} / {score.location_match.max_score}")
    print(f"   {score.location_match.explanation}")
    print(f"   Job: {score.location_match.metadata.get('job_location')}")
    print(f"   Candidate: {score.location_match.metadata.get('candidate_location')}")

    # JSON output
    print("\n" + "=" * 80)
    print("JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(score.to_dict(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("[OK] TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    test_deterministic_scoring()
