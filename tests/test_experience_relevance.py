"""
Test experience contextuelle: Chauffeur -> Senior Dev.
L'experience de chauffeur ne devrait PAS compter pour un poste de dev.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_agent import ScoringAgent


def test_experience_relevance():
    """Test experience contextuelle avec AI"""

    with open("test_cv_chauffeur.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    print("=" * 80)
    print("TEST: Experience Contextuelle - Chauffeur -> Senior Dev")
    print("=" * 80)
    print("\nBEFORE FIX:")
    print("  Total: 33.2/100")
    print("  Experience: 9.0/10 (12 years chauffeur counted for dev job!)")
    print("\nEXPECTED AFTER FIX:")
    print("  Total: 18-25/100")
    print("  Experience: 0-1/10 (chauffeur experience NOT relevant for dev)")
    print("\nCalculating (~50s)...\n")

    agent = ScoringAgent()

    match = agent.score_candidate(
        resume_text=resume,
        job_title="Senior Python Developer",
        company="Tech Corp Inc.",
        job_description="""We are looking for a Senior Python Developer to join our engineering team.
        You will design and build scalable backend systems, work with microservices architecture,
        and mentor junior developers. Strong Python, Docker, Kubernetes, and PostgreSQL skills required.
        Experience with FastAPI, async programming, and cloud platforms (AWS/GCP) highly valued.""",
        job_requirements=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL"],
        job_location="Remote / France",
        job_salary=130000,
        candidate_location="France",
        candidate_salary_expectation=40000,
        industry="tech"
    )

    print("\n" + "=" * 80)
    print("RESULTS AFTER EXPERIENCE RELEVANCE FIX")
    print("=" * 80)

    breakdown = match.score_breakdown

    print(f"\n[TOTAL SCORE]")
    print(f"  Before: 33.2/100")
    print(f"  After:  {match.match_score:.1f}/100")
    print(f"  Change: {match.match_score - 33.2:+.1f} pts")

    if match.match_score <= 25:
        print("  Status: [EXCELLENT] Correctly low score for mismatch!")
    elif match.match_score <= 30:
        print("  Status: [GOOD] Score improved significantly")
    else:
        print("  Status: [WARNING] Score still too high for mismatch")

    print(f"\n[EXPERIENCE DETAIL] {breakdown.deterministic.experience_years.score:.1f}/10")
    print(f"  Before: 9.0/10 (12 years counted)")
    print(f"  After:  {breakdown.deterministic.experience_years.score:.1f}/10")
    print(f"  Change: {breakdown.deterministic.experience_years.score - 9.0:+.1f} pts")
    print(f"\n  Explanation:")
    print(f"  {breakdown.deterministic.experience_years.explanation}")
    print(f"\n  Metadata:")
    print(f"  - Relevant years: {breakdown.deterministic.experience_years.metadata.get('resume_years', 'N/A')}")
    print(f"  - Semantic eval: {breakdown.deterministic.experience_years.metadata.get('semantic_evaluation', False)}")

    print(f"\n[DETERMINISTIC BREAKDOWN] {breakdown.deterministic.total:.1f}/40")
    print(f"  Experience:  {breakdown.deterministic.experience_years.score:4.1f}/10")
    print(f"  Skills:      {breakdown.deterministic.skills_matching.score:4.1f}/15")
    print(f"  Education:   {breakdown.deterministic.education_match.score:4.1f}/5")
    print(f"  Salary:      {breakdown.deterministic.salary_fit.score:4.1f}/5")
    print(f"  Location:    {breakdown.deterministic.location_match.score:4.1f}/5")

    print(f"\n[OTHER SCORES]")
    print(f"  Semantic:  {breakdown.semantic.total:.1f}/40")
    print(f"  Bonus:     {breakdown.bonus.total:.1f}/20")

    print(f"\n[RECOMMENDATION]")
    print(f"  {match.recommendation}")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    exp_change = breakdown.deterministic.experience_years.score - 9.0
    print(f"\nExperience score change: {exp_change:+.1f} pts")
    if exp_change <= -7:
        print("  [EXCELLENT] Chauffeur experience correctly scored as NOT relevant!")
    elif exp_change <= -5:
        print("  [GOOD] Significant improvement")
    else:
        print(f"  [WARNING] Expected -7 to -9 pts, got {exp_change:+.1f}")

    total_change = match.match_score - 33.2
    print(f"\nTotal score change: {total_change:+.1f} pts")
    if total_change <= -10:
        print("  [EXCELLENT] Major improvement for mismatch detection!")
    elif total_change <= -7:
        print("  [GOOD] Good reduction")
    else:
        print(f"  [INFO] Expected -8 to -15 pts reduction")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_experience_relevance()
