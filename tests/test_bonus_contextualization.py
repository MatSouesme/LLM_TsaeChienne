"""
Test bonus contextualization: Data Scientist -> Chauffeur.
Should score ML/AI skills as 0 points (irrelevant).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_agent import ScoringAgent


def test_bonus_contextualization():
    """Test bonus scores are contextualized by job relevance"""

    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    print("=" * 80)
    print("TEST: Data Scientist -> Chauffeur (Bonus Contextualization)")
    print("=" * 80)
    print("\nBEFORE FIX:")
    print("  Total: 46.0/100")
    print("  Bonus: 17.0/20")
    print("    - Rare Skills: 5/5 (ML/AI skills scored without context)")
    print("\nEXPECTED AFTER FIX:")
    print("  Total: 20-30/100")
    print("  Bonus: 5-8/20")
    print("    - Rare Skills: 0-1/5 (ML/AI irrelevant for chauffeur)")
    print("\nCalculating (~50s)...\n")

    agent = ScoringAgent()

    match = agent.score_candidate(
        resume_text=resume,
        job_title="Chauffeur Poids Lourd - Longue Distance",
        company="TransEurope Logistics",
        job_description="""Recherche chauffeur poids lourd experimente pour routes internationales Europe.
        Permis C + FIMO requis. Trajets longue distance, livraisons regulieres Allemagne, Belgique, Italie.
        Respect des temps de conduite, maintenance vehicule. Hebergement paye en deplacement.""",
        job_requirements=["Permis C", "FIMO", "Carte conducteur", "Experience route", "Ponctualite", "Autonomie"],
        job_location="Paris / France",
        job_salary=42000,
        candidate_location="France",
        candidate_salary_expectation=65000,
        industry="health"
    )

    print("\n" + "=" * 80)
    print("RESULTS AFTER BONUS CONTEXTUALIZATION FIX")
    print("=" * 80)

    breakdown = match.score_breakdown

    print(f"\n[TOTAL SCORE]")
    print(f"  Before: 46.0/100")
    print(f"  After:  {match.match_score:.1f}/100")
    print(f"  Change: {match.match_score - 46.0:+.1f} pts")

    if match.match_score <= 30:
        print("  Status: [EXCELLENT] Correctly low score for mismatched profile")
    elif match.match_score <= 40:
        print("  Status: [GOOD] Score improved but still room for reduction")
    else:
        print("  Status: [WARNING] Score still too high for Data Scientist->Chauffeur")

    print(f"\n[BONUS BREAKDOWN] {breakdown.bonus.total:.1f}/20")
    print(f"  Before: 17.0/20")
    print(f"  Change: {breakdown.bonus.total - 17.0:+.1f} pts")
    print(f"\n  Components:")
    print(f"    Industry Exp:  {breakdown.bonus.industry_experience.score:4.1f}/10")
    print(f"    Rare Skills:   {breakdown.bonus.rare_skills_premium.score:4.1f}/5 (was 5/5)")
    print(f"      -> {breakdown.bonus.rare_skills_premium.explanation}")
    print(f"    Career:        {breakdown.bonus.career_trajectory.score:4.1f}/5")

    print(f"\n[OTHER SCORES]")
    print(f"  Deterministic: {breakdown.deterministic.total:.1f}/40")
    print(f"  Semantic:      {breakdown.semantic.total:.1f}/40")

    print(f"\n[RECOMMENDATION]")
    print(f"  {match.recommendation}")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    rare_skills_change = breakdown.bonus.rare_skills_premium.score - 5.0
    print(f"\nRare Skills change: {rare_skills_change:+.1f} pts")
    if rare_skills_change <= -3:
        print("  [EXCELLENT] ML/AI skills correctly scored as irrelevant!")
    elif rare_skills_change <= -2:
        print("  [GOOD] Significant improvement in contextualization")
    else:
        print(f"  [WARNING] Expected -3 to -5 pts, got {rare_skills_change:+.1f}")

    total_change = match.match_score - 46.0
    print(f"\nTotal score change: {total_change:+.1f} pts")
    if total_change <= -10:
        print("  [OK] Good reduction for mismatched profile")
    else:
        print(f"  [INFO] Expected ~-10 to -20 pts reduction")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_bonus_contextualization()
