"""
Quick demo script for testing the Conversational Job Matching Agent.

Usage:
    python demo_agent.py
"""

import os
from dotenv import load_dotenv
from agents.conversational_agent import ConversationalJobAgent

# Load environment
load_dotenv()

# Sample job database (use your real JOB_DATABASE in production)
DEMO_JOBS = [
    {
        "title": "Senior Python Developer",
        "company": "FinTech Corp",
        "location": "Remote / France",
        "salary": 130000,
        "industry": "fintech",
        "description": "Python developer with ML experience for trading systems",
        "requirements": ["Python", "SQL", "Docker", "ML", "Trading"]
    },
    {
        "title": "Data Scientist",
        "company": "DataCo",
        "location": "Paris",
        "salary": 85000,
        "industry": "fintech",
        "description": "Data scientist for financial modeling",
        "requirements": ["Python", "ML", "Statistics", "SQL"]
    },
    {
        "title": "Junior Developer",
        "company": "Startup XYZ",
        "location": "Remote",
        "salary": 45000,
        "industry": "tech",
        "description": "Junior web developer",
        "requirements": ["Python", "JavaScript", "Git"]
    },
    {
        "title": "ML Engineer",
        "company": "AI Labs",
        "location": "Paris",
        "salary": 110000,
        "industry": "tech",
        "description": "ML engineer for NLP projects",
        "requirements": ["Python", "ML", "NLP", "Docker"]
    },
    {
        "title": "Backend Developer",
        "company": "Gaming Co",
        "location": "Remote",
        "salary": 95000,
        "industry": "gambling",
        "description": "Backend developer for gaming platform",
        "requirements": ["Python", "FastAPI", "PostgreSQL", "Redis"]
    }
]


def demo_scenario_1():
    """Demo: User provides all info at once"""
    print("\n" + "="*80)
    print("DEMO 1: User provides complete info upfront")
    print("="*80 + "\n")

    agent = ConversationalJobAgent(
        job_database=DEMO_JOBS,
        verbose=False  # Set to True to see agent reasoning
    )

    print("[USER]: I have 8 years of Python/ML experience. Looking for fintech jobs, remote, 100K+\n")

    response = agent.chat(
        session_id="demo1",
        user_message="I have 8 years of Python/ML experience. Looking for fintech jobs, remote, 100K+"
    )

    print(f"[AGENT]: {response['agent_response']}\n")
    print(f"[INFO] Collected profile: {response['collected_info']}\n")


def demo_scenario_2():
    """Demo: Multi-turn conversation with clarifications"""
    print("\n" + "="*80)
    print("DEMO 2: Multi-turn conversation with clarifications")
    print("="*80 + "\n")

    agent = ConversationalJobAgent(
        job_database=DEMO_JOBS,
        verbose=False
    )

    session_id = "demo2"

    # Turn 1
    print("[USER]: I need a new job\n")
    response1 = agent.chat(session_id, "I need a new job")
    print(f"[AGENT]: {response1['agent_response']}\n")
    print("-"*80 + "\n")

    # Turn 2
    print("[USER]: I'm interested in fintech\n")
    response2 = agent.chat(session_id, "I'm interested in fintech")
    print(f"[AGENT]: {response2['agent_response']}\n")
    print("-"*80 + "\n")

    # Turn 3
    print("[USER]: I prefer remote work\n")
    response3 = agent.chat(session_id, "I prefer remote work")
    print(f"[AGENT]: {response3['agent_response']}\n")
    print("-"*80 + "\n")

    # Turn 4
    print("[USER]: At least 100K\n")
    response4 = agent.chat(session_id, "At least 100K")
    print(f"[AGENT]: {response4['agent_response']}\n")

    # Session summary
    summary = agent.get_session_summary(session_id)
    print(f"[INFO] Messages exchanged: {summary['message_count']}")
    print(f"[INFO] Final profile: {summary['collected_info']}\n")


def demo_scenario_3():
    """Demo: Search with resume"""
    print("\n" + "="*80)
    print("DEMO 3: Search with resume provided")
    print("="*80 + "\n")

    resume = """
    John Doe
    Senior Software Engineer

    Experience:
    - 10 years as Software Engineer
    - Python, Machine Learning, Docker, SQL
    - Built trading systems and ML pipelines

    Education:
    - Master's in Computer Science

    Skills: Python, ML, Docker, SQL, Trading Systems
    """

    agent = ConversationalJobAgent(
        job_database=DEMO_JOBS,
        verbose=False
    )

    print("[USER]: Here's my resume. I'm looking for a senior role.\n")

    response = agent.chat(
        session_id="demo3",
        user_message="Here's my resume. I'm looking for a senior role.",
        resume_text=resume
    )

    print(f"[AGENT]: {response['agent_response']}\n")
    print(f"[INFO] Extracted profile: {response['collected_info']}\n")


def interactive_demo():
    """Interactive demo: Chat with the agent"""
    print("\n" + "="*80)
    print("INTERACTIVE DEMO: Chat with the Agent")
    print("="*80)
    print("Type 'quit' to exit, 'reset' to start new session\n")

    agent = ConversationalJobAgent(
        job_database=DEMO_JOBS,
        verbose=False  # Change to True to see reasoning
    )

    session_id = "interactive"

    while True:
        user_input = input("\n[YOU]: ").strip()

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            print("\nGoodbye!")
            break

        if user_input.lower() == 'reset':
            agent.reset_session(session_id)
            print("\n[SYSTEM] Session reset.\n")
            continue

        if user_input.lower() == 'summary':
            summary = agent.get_session_summary(session_id)
            print(f"\n[SYSTEM] Messages: {summary['message_count']}")
            print(f"[SYSTEM] Profile: {summary['collected_info']}\n")
            continue

        try:
            response = agent.chat(session_id, user_input)
            print(f"\n[AGENT]: {response['agent_response']}\n")
        except Exception as e:
            print(f"\n[ERROR]: {e}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "1":
            demo_scenario_1()
        elif mode == "2":
            demo_scenario_2()
        elif mode == "3":
            demo_scenario_3()
        elif mode == "interactive" or mode == "i":
            interactive_demo()
        else:
            print("Usage: python demo_agent.py [1|2|3|interactive]")
    else:
        # Run all demos
        print("\n🤖 CONVERSATIONAL JOB MATCHING AGENT - DEMO\n")

        demo_scenario_1()
        input("\nPress Enter to continue to Demo 2...")

        demo_scenario_2()
        input("\nPress Enter to continue to Demo 3...")

        demo_scenario_3()

        print("\n" + "="*80)
        print("All demos completed! 🎉")
        print("="*80)
        print("\nTry interactive mode: python demo_agent.py interactive")
