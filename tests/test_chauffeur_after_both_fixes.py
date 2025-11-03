"""
Test Jean-Pierre après TOUS les fixes (expérience + skills).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_agent import ScoringAgent


def test_chauffeur_after_all_fixes():
    """Test Chauffeur après corrections expérience + skills"""

    with open("test_cv_chauffeur.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    print("=" * 80)
    print("TEST: Chauffeur AFTER ALL FIXES (Experience + Skills)")
    print("=" * 80)
    print("\nBEFORE:")
    print("  Total: 72.7/100")
    print("  - Deterministic: 22.7/40")
    print("    * Experience: 0/10")
    print("    * Skills: 7.7/15")
    print("\nEXPECTED AFTER:")
    print("  Total: 82-88/100")
    print("  - Deterministic: 32-35/40")
    print("    * Experience: ~10/10 (12 years)")
    print("    * Skills: ~10-12/15 (4/6 matched)")
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
        candidate_salary_expectation=40000,
        industry="health"
    )

    print("\n" + "=" * 80)
    print("RESULTS AFTER ALL FIXES")
    print("=" * 80)

    breakdown = match.score_breakdown

    print(f"\n[TOTAL SCORE]")
    print(f"  Before: 72.7/100")
    print(f"  After:  {match.match_score:.1f}/100")
    print(f"  Gain:   {match.match_score - 72.7:+.1f} pts")

    if match.match_score >= 82:
        print("  Status: [EXCELLENT] Target reached!")
    elif match.match_score >= 75:
        print("  Status: [GOOD] Significant improvement")
    else:
        print("  Status: [MODERATE] Still room for improvement")

    print(f"\n[DETERMINISTIC] {breakdown.deterministic.total:.1f}/40")
    print(f"  Before: 22.7/40")
    print(f"  Gain:   {breakdown.deterministic.total - 22.7:+.1f} pts")
    print(f"\n  Components:")
    print(f"    Experience:  {breakdown.deterministic.experience_years.score:4.1f}/10 (was 0/10, +{breakdown.deterministic.experience_years.score:.1f})")
    print(f"      -> {breakdown.deterministic.experience_years.explanation}")
    print(f"    Skills:      {breakdown.deterministic.skills_matching.score:4.1f}/15 (was 7.7/15, +{breakdown.deterministic.skills_matching.score - 7.7:.1f})")
    print(f"      -> Matched: {breakdown.deterministic.skills_matching.metadata.get('matched_skills', [])}")
    print(f"    Education:   {breakdown.deterministic.education_match.score:4.1f}/5")
    print(f"    Salary:      {breakdown.deterministic.salary_fit.score:4.1f}/5")
    print(f"    Location:    {breakdown.deterministic.location_match.score:4.1f}/5")

    print(f"\n[SEMANTIC] {breakdown.semantic.total:.1f}/40")
    print(f"  Before: 33.0/40")
    print(f"  Change: {breakdown.semantic.total - 33.0:+.1f} pts")

    print(f"\n[BONUS] {breakdown.bonus.total:.1f}/20")
    print(f"  Before: 17.0/20")
    print(f"  Change: {breakdown.bonus.total - 17.0:+.1f} pts")

    print(f"\n[RECOMMENDATION]")
    print(f"  {match.recommendation}")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    det_gain = breakdown.deterministic.total - 22.7
    print(f"\nDeterministic gain: +{det_gain:.1f} pts")
    if det_gain >= 8:
        print("  [OK] Significant improvement from fixes")
    else:
        print("  [WARNING] Expected +8-12 pts, got +{det_gain:.1f}")

    total_gain = match.match_score - 72.7
    print(f"\nTotal gain: +{total_gain:.1f} pts")
    if total_gain >= 8:
        print("  [OK] Mission accomplished!")
    else:
        print("  [WARNING] Expected +8-15 pts")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_chauffeur_after_all_fixes()
