import sys
from pathlib import Path

# Ensure project root is on sys.path so 'storage' package can be imported when
# running this script from the scripts/ directory.
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from storage.offers_db import add_offer, list_offers

# Five sample offers to seed the database
samples = [
    {
        "title": "Junior Python Developer",
        "company": "DevStart",
        "location": "Paris",
        "salary": 40000,
        "industry": "tech",
        "description": "Entry-level Python developer to work on backend services and APIs.",
        "requirements": ["Python", "Git", "REST APIs"]
    },
    {
        "title": "Senior Data Analyst",
        "company": "Market Insights",
        "location": "Lyon",
        "salary": 65000,
        "industry": "fintech",
        "description": "Analyze large marketing datasets and build dashboards for stakeholders.",
        "requirements": ["SQL", "Python", "Tableau"]
    },
    {
        "title": "Customer Support Specialist",
        "company": "HelpWise",
        "location": "Remote",
        "salary": 30000,
        "industry": "ecommerce",
        "description": "Provide friendly customer support via email and chat.",
        "requirements": ["Communication", "Empathy", "CRM"]
    },
    {
        "title": "DevOps Engineer",
        "company": "InfraCloud",
        "location": "Paris / Remote",
        "salary": 90000,
        "industry": "tech",
        "description": "Maintain CI/CD pipelines and cloud infrastructure.",
        "requirements": ["Kubernetes", "Terraform", "Docker", "AWS"]
    },
    {
        "title": "Hospitality Manager",
        "company": "GrandStay Hotels",
        "location": "Nice",
        "salary": 45000,
        "industry": "health",
        "description": "Manage daily operations of a boutique hotel, supervise staff.",
        "requirements": ["Management", "Customer Service", "Scheduling"]
    }
]

inserted = []
for s in samples:
    oid = add_offer(
        s["title"], s["company"], s["location"], s["salary"], s["industry"], s["description"], s["requirements"], None, None
    )
    print(f"Inserted offer id: {oid} - {s['title']} @ {s['company']}")
    inserted.append(oid)

print('\nCurrent offers in DB:')
for o in list_offers():
    print(o)

print('\nDone.')
