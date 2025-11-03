"""
Test Jean-Pierre après fix extraction expérience.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_agent import ScoringAgent


def test_chauffeur_after_experience_fix():
    """Test Chauffeur → Chauffeur après correction expérience"""

    with open("test_cv_chauffeur.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    print("=" * 80)
    print("TEST: Chauffeur to Chauffeur (AFTER FIX EXPERIENCE)")
    print("=" * 80)
    print("\nBefore fix: 72.7/100")
    print("Expected after fix: 82-90/100 (gain +10 pts experience)")
    print("\nCalculation en cours (~50s)...\n")

    agent = ScoringAgent()

    match = agent.score_candidate(
        resume_text=resume,
        job_title="Chauffeur Poids Lourd - Longue Distance",
        company="TransEurope Logistics",
        job_description="""Recherche chauffeur poids lourd expérimenté pour routes internationales Europe.
        Permis C + FIMO requis. Trajets longue distance, livraisons régulières Allemagne, Belgique, Italie.
        Respect des temps de conduite, maintenance véhicule. Hébergement payé en déplacement.""",
        job_requirements=["Permis C", "FIMO", "Carte conducteur", "Expérience route", "Ponctualité", "Autonomie"],
        job_location="Paris / France",
        job_salary=42000,
        candidate_location="France",
        candidate_salary_expectation=40000,
        industry="health"
    )

    print("\n" + "=" * 80)
    print("RÉSULTATS")
    print("=" * 80)

    print(f"\n[SCORE] {match.match_score:.1f}/100")
    print(f"  Avant: 72.7/100")
    print(f"  Après: {match.match_score:.1f}/100")
    print(f"  Gain: {match.match_score - 72.7:+.1f} pts")

    breakdown = match.score_breakdown

    print(f"\n[BREAKDOWN]")
    print(f"  Deterministic: {breakdown.deterministic.total:.1f}/40 (before: 22.7/40)")
    print(f"    - Experience: {breakdown.deterministic.experience_years.score:.1f}/10 (before: 0/10)")
    print(f"    - Skills: {breakdown.deterministic.skills_matching.score:.1f}/15")
    print(f"    - Education: {breakdown.deterministic.education_match.score:.1f}/5")
    print(f"    - Salary: {breakdown.deterministic.salary_fit.score:.1f}/5")
    print(f"    - Location: {breakdown.deterministic.location_match.score:.1f}/5")

    print(f"\n  Semantic: {breakdown.semantic.total:.1f}/40 (before: 33.0/40)")
    print(f"  Bonus: {breakdown.bonus.total:.1f}/20 (before: 17.0/20)")

    print(f"\n[EXPERIENCE DETAIL]")
    print(f"  {breakdown.deterministic.experience_years.explanation}")
    print(f"  Years detected: {breakdown.deterministic.experience_years.metadata.get('resume_years', 'N/A')}")

    print(f"\n[RECOMMENDATION]")
    print(f"  {match.recommendation}")

    print("\n" + "=" * 80)

    # Analyse
    if match.match_score >= 80:
        print("[OK] Score target atteint! (>=80/100)")
    elif match.match_score >= 75:
        print("[GOOD] Score amélioré mais peut encore progresser")
    else:
        print("[WARNING] Score encore sous target. Skills extraction à corriger.")

    print("=" * 80)


if __name__ == "__main__":
    test_chauffeur_after_experience_fix()
