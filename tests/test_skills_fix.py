"""
Test amélioration extraction skills.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.deterministic_scoring_tool import DeterministicScoringTool


def test_skills_matching():
    """Test smart skill matching"""

    print("=" * 80)
    print("TEST: Smart Skills Matching")
    print("=" * 80)

    tool = DeterministicScoringTool()

    # Test avec Jean-Pierre
    with open("test_cv_chauffeur.txt", "r", encoding="utf-8") as f:
        cv = f.read()

    print("\n[CV JEAN-PIERRE - Chauffeur]")
    print("\nCV contains:")
    print("- Permis B, C, CE")
    print("- FIMO / FCO")
    print("- Carte conducteur digitale")

    print("\nJob Requirements:")
    requirements = ["Permis C", "FIMO", "Carte conducteur", "Experience route", "Ponctualite", "Autonomie"]
    for req in requirements:
        print(f"  - {req}")

    print("\n[TESTING MATCHES]")
    for req in requirements:
        match = tool._smart_skill_match(req, cv)
        print(f"  {req:25s} : {'[MATCH]' if match else '[MISS]'}")

    print("\n" + "-" * 80)

    # Test scoring complet
    print("\n[FULL SCORING TEST]")

    job_requirements = ["Permis C", "FIMO", "Carte conducteur", "Experience route", "Ponctualite", "Autonomie"]
    job_description = "Chauffeur poids lourd"

    score_detail = tool._score_skills_matching(cv, job_requirements, job_description)

    print(f"\nScore: {score_detail.score:.1f}/15")
    print(f"Explanation: {score_detail.explanation}")
    print(f"\nMatched ({len(score_detail.metadata['matched_skills'])}):")
    for skill in score_detail.metadata['matched_skills']:
        print(f"  + {skill}")
    print(f"\nMissing ({len(score_detail.metadata['missing_skills'])}):")
    for skill in score_detail.metadata['missing_skills']:
        print(f"  - {skill}")

    print("\n" + "=" * 80)

    # Expected: 6/6 skills matched = 15/15 points
    if score_detail.score >= 13:
        print("[OK] Excellent skills matching!")
    elif score_detail.score >= 10:
        print("[GOOD] Good skills matching")
    else:
        print(f"[WARNING] Score still low: {score_detail.score:.1f}/15")

    print("=" * 80)


if __name__ == "__main__":
    test_skills_matching()
