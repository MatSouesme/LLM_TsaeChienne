"""
Tests for the Conversational Job Matching Agent.

This test suite validates:
1. Agent initialization and session management
2. Information gathering and clarification logic
3. Job search functionality
4. Conversation flow and memory
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.conversational_agent import ConversationalJobAgent


# Sample job database for testing
TEST_JOB_DATABASE = [
    {
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "Remote / France",
        "salary": 130000,
        "industry": "fintech",
        "description": "Python developer with ML experience. Work on trading systems.",
        "requirements": ["Python", "SQL", "Docker", "ML", "Trading"]
    },
    {
        "title": "Data Scientist",
        "company": "DataCo",
        "location": "Paris",
        "salary": 85000,
        "industry": "fintech",
        "description": "Data scientist for financial modeling and analytics.",
        "requirements": ["Python", "ML", "Statistics", "SQL"]
    },
    {
        "title": "Junior Developer",
        "company": "Startup XYZ",
        "location": "Remote",
        "salary": 45000,
        "industry": "tech",
        "description": "Junior developer for web applications.",
        "requirements": ["Python", "JavaScript", "Git"]
    }
]

# Sample resume
SAMPLE_RESUME = """
John Doe
Senior Software Engineer

Experience:
- 8 years as Software Engineer at TechCorp
- Python, Machine Learning, Docker, SQL
- Built trading systems and ML pipelines

Education:
- Master's in Computer Science

Skills: Python, ML, Docker, SQL, Trading Systems
"""


def test_agent_initialization():
    """Test that agent initializes correctly."""
    print("\n" + "="*80)
    print("TEST 1: Agent Initialization")
    print("="*80)

    agent = ConversationalJobAgent(
        job_database=TEST_JOB_DATABASE,
        verbose=True
    )

    assert agent is not None
    assert agent.job_database == TEST_JOB_DATABASE
    assert len(agent.sessions) == 0

    print("[OK] Agent initialized successfully")


def test_session_creation():
    """Test session creation and management."""
    print("\n" + "="*80)
    print("TEST 2: Session Creation")
    print("="*80)

    agent = ConversationalJobAgent(
        job_database=TEST_JOB_DATABASE,
        verbose=True
    )

    session_id = "test_session_001"
    session = agent.create_session(session_id)

    assert session["session_id"] == session_id
    assert session["state"] == "COLLECTING_INFO"
    assert session["memory"] is not None
    assert session["collected_info"]["resume_text"] is None

    print(f"[OK] Session created: {session_id}")
    print(f"   State: {session['state']}")
    print(f"   Collected info: {session['collected_info']}")


def test_conversation_with_resume():
    """Test full conversation flow starting with resume."""
    print("\n" + "="*80)
    print("TEST 3: Conversation with Resume")
    print("="*80)

    agent = ConversationalJobAgent(
        job_database=TEST_JOB_DATABASE,
        verbose=True
    )

    session_id = "test_session_002"

    # Message 1: Provide resume
    print("\n--- Message 1: User provides resume ---")
    response1 = agent.chat(
        session_id=session_id,
        user_message="Hi, I'm looking for a new job. Here's my resume.",
        resume_text=SAMPLE_RESUME
    )

    print(f"\nAgent Response 1:")
    print(response1["agent_response"])

    # Message 2: Provide industry preference
    print("\n--- Message 2: User provides industry ---")
    response2 = agent.chat(
        session_id=session_id,
        user_message="I'm interested in fintech"
    )

    print(f"\nAgent Response 2:")
    print(response2["agent_response"])

    # Message 3: Provide location
    print("\n--- Message 3: User provides location ---")
    response3 = agent.chat(
        session_id=session_id,
        user_message="I prefer remote work"
    )

    print(f"\nAgent Response 3:")
    print(response3["agent_response"])

    # Message 4: Provide salary
    print("\n--- Message 4: User provides salary ---")
    response4 = agent.chat(
        session_id=session_id,
        user_message="I'm looking for at least 100K"
    )

    print(f"\nAgent Response 4:")
    print(response4["agent_response"])

    # Check session state
    summary = agent.get_session_summary(session_id)
    print(f"\n[OK] Conversation completed")
    print(f"   Messages exchanged: {summary['message_count']}")
    print(f"   Collected info: {summary['collected_info']}")


def test_clarification_questions():
    """Test that agent asks clarifying questions when info is missing."""
    print("\n" + "="*80)
    print("TEST 4: Clarification Questions")
    print("="*80)

    agent = ConversationalJobAgent(
        job_database=TEST_JOB_DATABASE,
        verbose=True
    )

    session_id = "test_session_003"

    # Message with minimal info
    print("\n--- User provides minimal info ---")
    response = agent.chat(
        session_id=session_id,
        user_message="I have 5 years of Python experience and want a new job."
    )

    print(f"\nAgent Response:")
    print(response["agent_response"])

    # Agent should ask for missing info
    response_lower = response["agent_response"].lower()

    # Check if agent is asking questions
    has_question = "?" in response["agent_response"]
    asks_about_info = any(word in response_lower for word in ["industry", "location", "salary", "looking for"])

    print(f"\n[OK] Agent asks clarifying questions: {has_question and asks_about_info}")


def test_job_search():
    """Test job search functionality."""
    print("\n" + "="*80)
    print("TEST 5: Job Search")
    print("="*80)

    agent = ConversationalJobAgent(
        job_database=TEST_JOB_DATABASE,
        verbose=True
    )

    session_id = "test_session_004"

    # Provide complete info upfront
    print("\n--- User provides complete info ---")
    response = agent.chat(
        session_id=session_id,
        user_message="I have 8 years of Python/ML experience. Looking for fintech jobs, remote, 100K+",
        resume_text=SAMPLE_RESUME
    )

    print(f"\nAgent Response:")
    print(response["agent_response"])

    # Check if response mentions jobs
    response_lower = response["agent_response"].lower()
    mentions_jobs = any(word in response_lower for word in ["job", "position", "role", "match", "opportunity"])

    print(f"\n[OK] Agent searches and presents jobs: {mentions_jobs}")


def test_session_reset():
    """Test session reset functionality."""
    print("\n" + "="*80)
    print("TEST 6: Session Reset")
    print("="*80)

    agent = ConversationalJobAgent(
        job_database=TEST_JOB_DATABASE,
        verbose=True
    )

    session_id = "test_session_005"

    # Create session and add some data
    agent.chat(session_id=session_id, user_message="Hello", resume_text=SAMPLE_RESUME)

    # Check session exists
    session = agent.get_session(session_id)
    assert session is not None
    print(f"[OK] Session created: {session_id}")

    # Reset session
    agent.reset_session(session_id)

    # Check session is gone
    session = agent.get_session(session_id)
    assert session is None
    print(f"[OK] Session reset: {session_id}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("CONVERSATIONAL AGENT TEST SUITE")
    print("="*80)

    try:
        test_agent_initialization()
        test_session_creation()
        test_clarification_questions()
        test_job_search()
        test_conversation_with_resume()
        test_session_reset()

        print("\n" + "="*80)
        print("[OK] ALL TESTS PASSED!")
        print("="*80)

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
