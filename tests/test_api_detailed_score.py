"""
Test script for the detailed score API endpoint.
"""

import requests
import json


def test_detailed_score_api():
    """Test the /api/detailed-score endpoint"""

    # Read test resume
    with open("test_cv_maths_tech.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()

    print("=" * 80)
    print("TEST: Detailed Score API Endpoint")
    print("=" * 80)

    # Prepare request
    url = "http://localhost:8000/api/detailed-score"

    data = {
        "resume_text": resume_text,
        "job_title": "Senior Python Developer",
        "company": "Tech Corp Inc.",
        "industry": "gambling",
        "location": "Paris",
        "salary": 120000
    }

    print("\n[REQUEST]")
    print(f"URL: {url}")
    print(f"Job: {data['job_title']} at {data['company']}")
    print(f"Industry: {data['industry']}")
    print(f"Location: {data['location']}")
    print(f"Salary: €{data['salary']:,}")

    print("\n[STATUS] Sending request (this will take ~60 seconds)...")

    try:
        # Send request
        response = requests.post(url, data=data, timeout=180)

        if response.status_code == 200:
            result = response.json()

            print("\n" + "=" * 80)
            print("RESPONSE RECEIVED")
            print("=" * 80)

            print(f"\n[JOB] {result['job_title']} at {result['company']}")
            print(f"      Location: {result['location']}")
            print(f"      Salary: €{result['salary']:,}")

            print(f"\n[SCORE] Overall Match: {result['match_score']:.1f}/100")

            breakdown = result['score_breakdown']

            print("\n" + "-" * 80)
            print("SCORE BREAKDOWN:")
            print("-" * 80)

            print(f"\n1. DETERMINISTIC: {breakdown['deterministic']['total']:.1f}/40")
            for key, value in breakdown['deterministic']['details'].items():
                print(f"   - {key}: {value['score']:.1f}/{value['max']}")

            print(f"\n2. SEMANTIC: {breakdown['semantic']['total']:.1f}/40")
            for key, value in breakdown['semantic']['details'].items():
                print(f"   - {key}: {value['score']:.1f}/{value['max']}")

            print(f"\n3. BONUS: {breakdown['bonus']['total']:.1f}/20")
            for key, value in breakdown['bonus']['details'].items():
                print(f"   - {key}: {value['score']:.1f}/{value['max']}")

            print("\n" + "-" * 80)
            print("ANALYSIS:")
            print("-" * 80)

            print(f"\n[EXPLANATION]")
            print(f"{result['overall_explanation']}")

            print(f"\n[STRENGTHS]")
            for i, strength in enumerate(result['strengths'], 1):
                print(f"  {i}. {strength}")

            print(f"\n[WEAKNESSES]")
            for i, weakness in enumerate(result['weaknesses'], 1):
                print(f"  {i}. {weakness}")

            print(f"\n[RECOMMENDATION]")
            print(f"{result['recommendation']}")

            print("\n" + "=" * 80)
            print("[OK] TEST COMPLETED SUCCESSFULLY")
            print("=" * 80)

        else:
            print(f"\n[ERROR] Request failed with status {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out (>180 seconds)")
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to server")
        print("Make sure the server is running: python backend.py")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")


if __name__ == "__main__":
    test_detailed_score_api()
