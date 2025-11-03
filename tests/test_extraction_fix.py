"""
Test des corrections d'extraction.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.deterministic_scoring_tool import DeterministicScoringTool


def test_experience_extraction():
    """Test extraction d'expérience depuis dates"""

    print("=" * 80)
    print("TEST 1: Extraction Expérience depuis Dates")
    print("=" * 80)

    tool = DeterministicScoringTool()

    # Test avec Jean-Pierre
    with open("test_cv_chauffeur.txt", "r", encoding="utf-8") as f:
        cv_jean_pierre = f.read()

    print("\n[CV JEAN-PIERRE]")
    print("Expected: 12 ans (2012-2024)")
    print("- Chauffeur routier (2015-2024) = 9 ans")
    print("- Livreur VL (2012-2015) = 3 ans")

    years = tool._extract_experience_from_dates(cv_jean_pierre)
    print(f"\n[RESULT] Extracted: {years} years")

    if years >= 10:
        print("[OK] Correct extraction!")
    else:
        print(f"[WARNING] Expected ~12 years, got {years}")

    # Test avec Sandrine
    with open("test_cv_menage.txt", "r", encoding="utf-8") as f:
        cv_sandrine = f.read()

    print("\n" + "-" * 80)
    print("\n[CV SANDRINE]")
    print("Expected: 9 ans (2015-2024)")
    print("- Agent d'Entretien (2020-2024) = 4 ans")
    print("- Femme de Ménage (2017-2020) = 3 ans")
    print("- Aide à domicile (2015-2017) = 2 ans")

    years = tool._extract_experience_from_dates(cv_sandrine)
    print(f"\n[RESULT] Extracted: {years} years")

    if years >= 8:
        print("[OK] Correct extraction!")
    else:
        print(f"[WARNING] Expected ~9 years, got {years}")

    # Test avec Marie (Data Scientist)
    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        cv_marie = f.read()

    print("\n" + "-" * 80)
    print("\n[CV MARIE]")
    print("Expected: 2-3 ans")
    print("- Data Scientist (2022-2024) = 2 ans")
    print("- Research Intern (2021-2022) = 1 an")

    years = tool._extract_experience_from_dates(cv_marie)
    print(f"\n[RESULT] Extracted: {years} years")

    if 2 <= years <= 4:
        print("[OK] Correct extraction!")
    else:
        print(f"[WARNING] Expected ~3 years, got {years}")

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_experience_extraction()
