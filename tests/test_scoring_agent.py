"""
Test script for the complete scoring agent.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_agent import ScoringAgent


def test_scoring_agent():
    """Test the complete scoring agent with a sample resume and job."""

    # Read test resume
    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()

    print("=" * 80)
    print("TEST: Complete Scoring Agent")
    print("=" * 80)
    print(f"\nResume preview (first 300 chars):\n{resume_text[:300]}...")

    # Sample job data (from backend.py - Senior Python Developer in fintech)
    job_title = "Senior Python Developer"
    company = "Tech Innovators Inc."
    industry = "fintech"

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
    - Experience in financial services or fintech is a plus
    - Knowledge of AI/ML for financial applications is valuable

    We value:
    - Strong communication skills and teamwork
    - Problem-solving mindset
    - Initiative and ownership
    - Continuous learning
    - Collaborative work environment

    We offer competitive salary (€130,000) and remote work options.
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

    job_location = "Paris / Remote"
    job_salary = 130000
    candidate_location = "Paris"
    candidate_salary = 120000

    # Initialize scoring agent
    print("\n" + "=" * 80)
    print("INITIALIZING SCORING AGENT...")
    print("=" * 80)

    try:
        agent = ScoringAgent()
        print("[OK] Scoring agent initialized with all tools")
    except ValueError as e:
        print(f"[ERROR] {e}")
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    # Score the candidate
    print("\n" + "=" * 80)
    print("SCORING CANDIDATE (this will take ~60 seconds)...")
    print("=" * 80)
    print()

    detailed_match = agent.score_candidate(
        resume_text=resume_text,
        job_title=job_title,
        company=company,
        job_description=job_description,
        job_requirements=job_requirements,
        job_location=job_location,
        job_salary=job_salary,
        candidate_location=candidate_location,
        candidate_salary_expectation=candidate_salary,
        industry=industry,
        company_culture=company_culture
    )

    # Display results
    print("\n" + "=" * 80)
    print("COMPLETE MATCH REPORT")
    print("=" * 80)

    print(f"\n[JOB] {detailed_match.job_title} at {detailed_match.company}")
    print(f"      Location: {detailed_match.location}")
    print(f"      Salary: €{detailed_match.salary:,}")

    print(f"\n[SCORE] Overall Match: {detailed_match.match_score:.1f}/100")
    print(f"        Quality: {'Excellent' if detailed_match.match_score >= 80 else 'Good' if detailed_match.match_score >= 65 else 'Moderate'}")

    print("\n" + "-" * 80)
    print("SCORE BREAKDOWN:")
    print("-" * 80)

    breakdown = detailed_match.score_breakdown

    print(f"\n1. DETERMINISTIC SCORE: {breakdown.deterministic.total:.1f}/40")
    print(f"   - Skills Matching:  {breakdown.deterministic.skills_matching.score:.1f}/15")
    print(f"   - Experience Years: {breakdown.deterministic.experience_years.score:.1f}/10")
    print(f"   - Education Match:  {breakdown.deterministic.education_match.score:.1f}/5")
    print(f"   - Salary Fit:       {breakdown.deterministic.salary_fit.score:.1f}/5")
    print(f"   - Location Match:   {breakdown.deterministic.location_match.score:.1f}/5")

    print(f"\n2. SEMANTIC SCORE: {breakdown.semantic.total:.1f}/40")
    print(f"   - Soft Skills Match:  {breakdown.semantic.soft_skills_match.score:.1f}/15")
    print(f"   - Culture Fit:        {breakdown.semantic.culture_fit.score:.1f}/10")
    print(f"   - Growth Potential:   {breakdown.semantic.growth_potential.score:.1f}/10")
    print(f"   - Project Relevance:  {breakdown.semantic.project_relevance.score:.1f}/5")

    print(f"\n3. BONUS SCORE: {breakdown.bonus.total:.1f}/20")
    print(f"   - Industry Experience: {breakdown.bonus.industry_experience.score:.1f}/10")
    print(f"   - Rare Skills Premium: {breakdown.bonus.rare_skills_premium.score:.1f}/5")
    print(f"   - Career Trajectory:   {breakdown.bonus.career_trajectory.score:.1f}/5")

    print("\n" + "-" * 80)
    print("ANALYSIS:")
    print("-" * 80)

    print(f"\n[EXPLANATION]")
    print(f"{detailed_match.overall_explanation}")

    print(f"\n[STRENGTHS]")
    for i, strength in enumerate(detailed_match.strengths, 1):
        print(f"  {i}. {strength}")

    print(f"\n[WEAKNESSES]")
    for i, weakness in enumerate(detailed_match.weaknesses, 1):
        print(f"  {i}. {weakness}")

    print(f"\n[RECOMMENDATION]")
    print(f"{detailed_match.recommendation}")

    # JSON output
    print("\n" + "=" * 80)
    print("FULL JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(detailed_match.to_dict(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("[OK] TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Candidate: Marie Dupont (Data Scientist/ML Engineer)")
    print(f"Position:  {job_title} at {company}")
    print(f"Score:     {detailed_match.match_score:.1f}/100")
    print(f"Result:    {detailed_match.recommendation}")


if __name__ == "__main__":
    test_scoring_agent()
