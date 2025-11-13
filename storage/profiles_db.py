"""
Profile persistence using SQLite database.

This module provides CRUD operations for storing candidate profiles
persistently, allowing sessions to survive backend restarts.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "data"
DB_PATH = DB_DIR / "profiles.db"


def init_profiles_db() -> None:
    """Initialize the profiles database with required tables."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Profiles table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        session_id TEXT PRIMARY KEY,
        profile_data TEXT NOT NULL,
        state TEXT DEFAULT 'INITIAL',
        completeness_score INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Conversation history table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES profiles(session_id)
    );
    """)

    # Create index for faster lookups
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_session_id
    ON conversations(session_id);
    """)

    conn.commit()
    conn.close()


def save_profile(session_id: str, profile_data: Dict[str, Any],
                 state: str = 'INITIAL', completeness_score: int = 0) -> bool:
    """
    Save or update a profile in the database.

    Args:
        session_id: Unique session identifier
        profile_data: Profile dictionary with skills, experience, etc.
        state: Current state (INITIAL, ANALYZING, OPTIMIZING, COMPLETE)
        completeness_score: Profile completeness (0-100)

    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        profile_json = json.dumps(profile_data)
        now = datetime.utcnow().isoformat()

        # Try to update first
        cur.execute("""
        UPDATE profiles
        SET profile_data = ?, state = ?, completeness_score = ?, updated_at = ?
        WHERE session_id = ?
        """, (profile_json, state, completeness_score, now, session_id))

        # If no rows updated, insert new
        if cur.rowcount == 0:
            cur.execute("""
            INSERT INTO profiles (session_id, profile_data, state, completeness_score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, profile_json, state, completeness_score, now, now))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False


def load_profile(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a profile from the database.

    Args:
        session_id: Session identifier

    Returns:
        Profile dictionary or None if not found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        SELECT profile_data, state, completeness_score, created_at, updated_at
        FROM profiles
        WHERE session_id = ?
        """, (session_id,))

        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'profile': json.loads(row[0]),
            'state': row[1],
            'completeness_score': row[2],
            'created_at': row[3],
            'updated_at': row[4]
        }
    except Exception as e:
        print(f"Error loading profile: {e}")
        return None


def delete_profile(session_id: str) -> bool:
    """
    Delete a profile and its conversation history.

    Args:
        session_id: Session identifier

    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Delete conversations first (foreign key)
        cur.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))

        # Delete profile
        cur.execute("DELETE FROM profiles WHERE session_id = ?", (session_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting profile: {e}")
        return False


def save_conversation_message(session_id: str, role: str, content: str) -> bool:
    """
    Save a conversation message to history.

    Args:
        session_id: Session identifier
        role: 'user' or 'agent'
        content: Message content

    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        now = datetime.utcnow().isoformat()

        cur.execute("""
        INSERT INTO conversations (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
        """, (session_id, role, content, now))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving message: {e}")
        return False


def load_conversation_history(session_id: str, limit: int = 50) -> List[Dict[str, str]]:
    """
    Load conversation history for a session.

    Args:
        session_id: Session identifier
        limit: Maximum number of messages to retrieve

    Returns:
        List of message dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        SELECT role, content, timestamp
        FROM conversations
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """, (session_id, limit))

        rows = cur.fetchall()
        conn.close()

        # Return in chronological order
        return [
            {'role': r[0], 'content': r[1], 'timestamp': r[2]}
            for r in reversed(rows)
        ]
    except Exception as e:
        print(f"Error loading conversation: {e}")
        return []


def list_all_profiles(limit: int = 100) -> List[Dict[str, Any]]:
    """
    List all profiles in the database.

    Args:
        limit: Maximum number of profiles to return

    Returns:
        List of profile summaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        SELECT session_id, state, completeness_score, created_at, updated_at
        FROM profiles
        ORDER BY updated_at DESC
        LIMIT ?
        """, (limit,))

        rows = cur.fetchall()
        conn.close()

        return [
            {
                'session_id': r[0],
                'state': r[1],
                'completeness_score': r[2],
                'created_at': r[3],
                'updated_at': r[4]
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error listing profiles: {e}")
        return []


def get_profile_stats() -> Dict[str, Any]:
    """
    Get statistics about stored profiles.

    Returns:
        Dictionary with stats
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Total profiles
        cur.execute("SELECT COUNT(*) FROM profiles")
        total = cur.fetchone()[0]

        # Average completeness
        cur.execute("SELECT AVG(completeness_score) FROM profiles")
        avg_completeness = cur.fetchone()[0] or 0

        # Profiles by state
        cur.execute("SELECT state, COUNT(*) FROM profiles GROUP BY state")
        by_state = dict(cur.fetchall())

        conn.close()

        return {
            'total_profiles': total,
            'average_completeness': round(avg_completeness, 1),
            'by_state': by_state
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {}


# Initialize database on import
init_profiles_db()
