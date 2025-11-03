"""
Comprehensive test suite for all CVs with various job profiles.
"""

import sys
from pathlib import Path
import json
import time

sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_agent import ScoringAgent


def print_separator(char="=", length=80):
    print(char * length)


def print_result_summary(match, test_name):
    """Print a summary of match results"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

    print(f"\n[JOB] {match.job_title} at {match.company}")
    print(f"      Salary: €{match.salary:,} | Location: {match.location}")

    print(f"\n[SCORE] {match.match_score:.1f}/100", end="")
    if match.match_score >= 85:
        print(" [EXCELLENT]")
    elif match.match_score >= 75:
        print(" [VERY GOOD]")
    elif match.match_score >= 65:
        print(" [GOOD]")
    elif match.match_score >= 50:
        print(" [MODERATE]")
    else:
        print(" [POOR]")

    breakdown = match.score_breakdown
    print(f"\n[BREAKDOWN]")
    print(f"  Deterministic: {breakdown.deterministic.total:5.1f}/40 ({breakdown.deterministic.total/40*100:.0f}%)")
    print(f"  Semantic:      {breakdown.semantic.total:5.1f}/40 ({breakdown.semantic.total/40*100:.0f}%)")
    print(f"  Bonus:         {breakdown.bonus.total:5.1f}/20 ({breakdown.bonus.total/20*100:.0f}%)")

    print(f"\n[STRENGTHS]")
    for i, strength in enumerate(match.strengths[:3], 1):
        print(f"  {i}. {strength}")

    print(f"\n[WEAKNESSES]")
    for i, weakness in enumerate(match.weaknesses[:3], 1):
        print(f"  {i}. {weakness}")

    print(f"\n[RECOMMENDATION]")
    print(f"  {match.recommendation}")

    print(f"\n{'='*80}\n")


def test_1_chauffeur_perfect_match():
    """Test: Jean-Pierre (Chauffeur) -> Chauffeur Poids Lourd (EXPECTED: Excellent match)"""

    with open("test_cv_chauffeur.txt", "r", encoding="utf-8") as f:
        resume = f.read()

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
        industry="health"  # Using health as per database
    )

    print_result_summary(match, "Test 1: Chauffeur to Chauffeur (Perfect Match)")

    return match


def test_2_menage_good_match():
    """Test: Sandrine (Ménage) -> Agent d'Entretien (EXPECTED: Good match)"""

    with open("test_cv_menage.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    agent = ScoringAgent()

    match = agent.score_candidate(
        resume_text=resume,
        job_title="Agent d'Entretien - Bureaux et Espaces Commerciaux",
        company="CleanPro Services",
        job_description="""Recherche agent d'entretien pour nettoyage bureaux et espaces commerciaux.
        Travail en horaires décalés (tôt matin ou soirée). Nettoyage sols, sanitaires, vitres, poubelles.
        Utilisation produits professionnels. Possibilité temps partiel ou temps plein.
        Débutants acceptés avec formation.""",
        job_requirements=["Rigueur", "Ponctualité", "Autonomie", "Sens du détail", "Bonne condition physique"],
        job_location="Paris",
        job_salary=28000,
        candidate_location="Paris",
        candidate_salary_expectation=21600,  # 1800€ net/mois ≈ 21.6K brut
        industry="health"
    )

    print_result_summary(match, "Test 2: Menage to Agent Entretien (Good Match)")

    return match


def test_3_menage_to_gouvernante():
    """Test: Sandrine (Menage) -> Gouvernante Hotel Luxe (EXPECTED: Moderate match - overqualified standards)"""

    with open("test_cv_menage.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    agent = ScoringAgent()

    match = agent.score_candidate(
        resume_text=resume,
        job_title="Gouvernante d'Hotel de Luxe",
        company="Hotel Le Grand Paris",
        job_description="""Hotel 5 etoiles recherche gouvernante experimentee.
        Supervision equipe menage (10 personnes), controle qualite chambres, gestion stocks linge et produits.
        Standards luxe tres eleves. Experience hotellerie haut de gamme requise.
        Horaires variables, disponibilite week-ends.""",
        job_requirements=["Experience hotellerie luxe", "Management equipe", "Rigueur", "Standards qualite", "Gestion stocks", "Langues (anglais)"],
        job_location="Paris",
        job_salary=35000,
        candidate_location="Paris",
        candidate_salary_expectation=21600,
        industry="health"
    )

    print_result_summary(match, "Test 3: Menage to Gouvernante Luxe (Stretch Match)")

    return match


def test_4_mismatch_tech_to_chauffeur():
    """Test: Marie (Data Scientist) -> Chauffeur (EXPECTED: Poor match)"""

    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    agent = ScoringAgent()

    match = agent.score_candidate(
        resume_text=resume,
        job_title="Chauffeur Poids Lourd - Longue Distance",
        company="TransEurope Logistics",
        job_description="""Recherche chauffeur poids lourd experimente pour routes internationales Europe.
        Permis C + FIMO requis. Trajets longue distance, livraisons regulieres Allemagne, Belgique, Italie.""",
        job_requirements=["Permis C", "FIMO", "Carte conducteur", "Experience route", "Ponctualite", "Autonomie"],
        job_location="Paris / France",
        job_salary=42000,
        candidate_location="Paris",
        candidate_salary_expectation=120000,
        industry="health"
    )

    print_result_summary(match, "Test 4: Data Scientist to Chauffeur (MISMATCH)")

    return match


def test_5_mismatch_chauffeur_to_tech():
    """Test: Jean-Pierre (Chauffeur) -> Senior Python Developer (EXPECTED: Poor match)"""

    with open("test_cv_chauffeur.txt", "r", encoding="utf-8") as f:
        resume = f.read()

    agent = ScoringAgent()

    match = agent.score_candidate(
        resume_text=resume,
        job_title="Senior Python Developer",
        company="Tech Corp Inc.",
        job_description="""We're seeking a Senior Python Developer with strong experience in trading systems,
        FinTech, and high-frequency data processing. Must have expertise in Python, SQL, Docker,
        and distributed systems.""",
        job_requirements=["Python", "SQL", "Docker", "Trading Systems", "FinTech"],
        job_location="Remote / France",
        job_salary=130000,
        candidate_location="France",
        candidate_salary_expectation=40000,
        industry="gambling"
    )

    print_result_summary(match, "Test 5: Chauffeur to Senior Dev (MISMATCH)")

    return match


def main():
    """Run all tests and generate report"""

    print("\n" + "="*80)
    print("COMPREHENSIVE CV TESTING SUITE")
    print("="*80)
    print("\nTesting 3 CVs with 5 scenarios:")
    print("  1. Perfect match (Chauffeur to Chauffeur)")
    print("  2. Good match (Menage to Agent Entretien)")
    print("  3. Stretch match (Menage to Gouvernante Luxe)")
    print("  4. Mismatch (Data Scientist to Chauffeur)")
    print("  5. Mismatch (Chauffeur to Senior Dev)")
    print("\nThis will take approximately 4-5 minutes...\n")

    results = {}
    start_time = time.time()

    try:
        # Test 1: Perfect match
        print("\n[1/5] Testing Chauffeur to Chauffeur...")
        results['test1'] = test_1_chauffeur_perfect_match()

        # Test 2: Good match
        print("\n[2/5] Testing Menage to Agent Entretien...")
        results['test2'] = test_2_menage_good_match()

        # Test 3: Stretch match
        print("\n[3/5] Testing Menage to Gouvernante Luxe...")
        results['test3'] = test_3_menage_to_gouvernante()

        # Test 4: Mismatch tech to chauffeur
        print("\n[4/5] Testing Data Scientist to Chauffeur (mismatch)...")
        results['test4'] = test_4_mismatch_tech_to_chauffeur()

        # Test 5: Mismatch chauffeur to tech
        print("\n[5/5] Testing Chauffeur to Senior Dev (mismatch)...")
        results['test5'] = test_5_mismatch_chauffeur_to_tech()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    print(f"\n[TIME]  Total: {elapsed:.1f}s ({elapsed/5:.1f}s per candidate)")
    print(f"[COST]  Estimated: ${len(results) * 0.03:.2f} (~$0.03 per candidate)\n")

    print("Score Summary:")
    print(f"  1. Chauffeur to Chauffeur:          {results['test1'].match_score:5.1f}/100 {'[OK]' if results['test1'].match_score >= 80 else '[LOW]'}")
    print(f"  2. Menage to Agent Entretien:       {results['test2'].match_score:5.1f}/100 {'[OK]' if results['test2'].match_score >= 75 else '[LOW]'}")
    print(f"  3. Menage to Gouvernante Luxe:      {results['test3'].match_score:5.1f}/100 {'[OK]' if results['test3'].match_score >= 60 else '[LOW]'}")
    print(f"  4. Data Scientist to Chauffeur:     {results['test4'].match_score:5.1f}/100 {'[OK]' if results['test4'].match_score <= 40 else '[HIGH-Should be lower]'}")
    print(f"  5. Chauffeur to Senior Dev:         {results['test5'].match_score:5.1f}/100 {'[OK]' if results['test5'].match_score <= 40 else '[HIGH-Should be lower]'}")

    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80)

    # Save results to JSON
    results_dict = {
        f"test{i}": {
            "score": match.match_score,
            "job_title": match.job_title,
            "company": match.company,
            "recommendation": match.recommendation,
            "breakdown": {
                "deterministic": match.score_breakdown.deterministic.total,
                "semantic": match.score_breakdown.semantic.total,
                "bonus": match.score_breakdown.bonus.total
            }
        }
        for i, match in enumerate(results.values(), 1)
    }

    with open("test_results_all_cvs.json", "w", encoding="utf-8") as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)

    print("\n[OK] Results saved to test_results_all_cvs.json")


if __name__ == "__main__":
    main()
