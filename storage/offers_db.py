import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "data"
DB_PATH = DB_DIR / "offers.db"
PDF_DIR = DB_DIR / "offers"


def init_db() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        salary INTEGER,
        industry TEXT,
        description TEXT,
        requirements TEXT,
        pdf_path TEXT,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()


def add_offer(title: str, company: str, location: str, salary: Optional[int],
              industry: str, description: str, requirements: List[str],
              pdf_bytes: Optional[bytes], pdf_filename: Optional[str]) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    req_json = json.dumps(requirements)
    cur.execute(
        """
        INSERT INTO offers (title, company, location, salary, industry, description, requirements, pdf_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, company, location, salary, industry, description, req_json, None, created_at)
    )
    offer_id = cur.lastrowid
    pdf_path = None
    if pdf_bytes and pdf_filename:
        safe_name = f"{offer_id}_{Path(pdf_filename).name}"
        pdf_path = str(PDF_DIR / safe_name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
    cur.execute("UPDATE offers SET pdf_path = ? WHERE id = ?", (pdf_path, offer_id))
    conn.commit()
    conn.close()
    return offer_id


def list_offers() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, company, location, salary, industry, created_at FROM offers ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "company": r[2], "location": r[3], "salary": r[4], "industry": r[5], "created_at": r[6]}
        for r in rows
    ]


def get_offer(offer_id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, company, location, salary, industry, description, requirements, pdf_path, created_at FROM offers WHERE id = ?", (offer_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "title": row[1],
        "company": row[2],
        "location": row[3],
        "salary": row[4],
        "industry": row[5],
        "description": row[6],
        "requirements": json.loads(row[7] or "[]"),
        "pdf_path": row[8],
        "created_at": row[9]
    }
