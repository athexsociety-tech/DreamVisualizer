"""
Dream Visualizer AI - Database Layer
SQLite with automatic schema creation.
"""

import json
import logging
import os
import pathlib
import sqlite3
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger("dream_visualizer.database")

# ── DB Path — tries project folder first, fallback to user home ────────────────
def _resolve_db_path() -> str:
    # 1. Explicit env variable — highest priority
    if os.environ.get("DREAM_DB_PATH"):
        return os.environ["DREAM_DB_PATH"]

    # 2. Try project folder (same dir as this file)
    project_dir = pathlib.Path(__file__).parent.resolve()
    candidate   = project_dir / "dreams.db"
    try:
        candidate.touch(exist_ok=True)
        return str(candidate)
    except (OSError, PermissionError):
        pass

    # 3. Fallback: user home directory (always writable on Windows)
    home_db = pathlib.Path.home() / "dream_visualizer_dreams.db"
    logger.warning("Cannot write to project folder — using home: %s", home_db)
    return str(home_db)

DB_PATH = _resolve_db_path()

# ── Schema ─────────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS dreams (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    dream_text      TEXT NOT NULL,
    mood            TEXT NOT NULL,
    emotion_score   REAL NOT NULL DEFAULT 0.0,
    summary         TEXT NOT NULL DEFAULT '',
    interpretation  TEXT NOT NULL DEFAULT '',
    symbols         TEXT NOT NULL DEFAULT '[]',
    dream_score     REAL NOT NULL DEFAULT 0.0,
    image_url       TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dreams_created_at ON dreams(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dreams_mood       ON dreams(mood);
"""


# ── Connection helper ──────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    logger.debug("Connecting to DB: %s", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Public API ─────────────────────────────────────────────────────────────────

def create_database() -> None:
    """Create tables and indexes if they don't exist."""
    logger.info("Initialising database at %s", DB_PATH)
    with _connect() as conn:
        conn.executescript(DDL)
    logger.info("Database ready at %s", DB_PATH)


def save_dream(
    title: str,
    dream_text: str,
    mood: str,
    emotion_score: float,
    summary: str,
    interpretation: str,
    symbols: list[str],
    dream_score: float,
    image_url: str = "",
) -> str:
    """Insert a dream record and return its new UUID."""
    dream_id     = str(uuid.uuid4())
    created_at   = datetime.utcnow().isoformat()
    symbols_json = json.dumps(symbols if isinstance(symbols, list) else [symbols])

    sql = """
        INSERT INTO dreams
            (id, title, dream_text, mood, emotion_score,
             summary, interpretation, symbols, dream_score, image_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with _connect() as conn:
        conn.execute(sql, (
            dream_id, title, dream_text, mood, emotion_score,
            summary, interpretation, symbols_json, dream_score, image_url, created_at,
        ))
    logger.info("Saved dream %s (%s)", dream_id, title)
    return dream_id


def get_all_dreams(limit: int = 50, offset: int = 0) -> list[dict]:
    """Return a list of dream dicts ordered by most-recent first."""
    sql = """
        SELECT * FROM dreams
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    with _connect() as conn:
        rows = conn.execute(sql, (limit, offset)).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_dream(dream_id: str) -> dict | None:
    """Return a single dream dict or None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM dreams WHERE id = ?", (dream_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def delete_dream(dream_id: str) -> bool:
    """Delete a dream by id. Returns True if a row was deleted."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM dreams WHERE id = ?", (dream_id,))
    deleted = cur.rowcount > 0
    if deleted:
        logger.info("Deleted dream %s", dream_id)
    return deleted


def get_statistics() -> dict[str, Any]:
    """Return raw aggregated statistics used by the analytics engine."""
    sql_main = """
        SELECT
            COUNT(*)           AS total_dreams,
            AVG(dream_score)   AS avg_dream_score,
            AVG(emotion_score) AS avg_emotion_score,
            MAX(created_at)    AS latest_dream,
            MIN(created_at)    AS earliest_dream
        FROM dreams
    """
    sql_moods = """
        SELECT mood, COUNT(*) AS cnt
        FROM dreams
        GROUP BY mood
        ORDER BY cnt DESC
    """
    sql_monthly = """
        SELECT
            strftime('%Y-%m', created_at) AS month,
            COUNT(*)                      AS count,
            AVG(dream_score)              AS avg_score
        FROM dreams
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """
    sql_symbols = "SELECT symbols FROM dreams"

    with _connect() as conn:
        main        = dict(conn.execute(sql_main).fetchone())
        moods       = [dict(r) for r in conn.execute(sql_moods).fetchall()]
        monthly     = [dict(r) for r in conn.execute(sql_monthly).fetchall()]
        symbol_rows = conn.execute(sql_symbols).fetchall()

    all_symbols: list[str] = []
    for row in symbol_rows:
        try:
            all_symbols.extend(json.loads(row["symbols"]))
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        **main,
        "mood_distribution": moods,
        "monthly_trends":    monthly,
        "all_symbols":       all_symbols,
    }


# ── Internal helpers ───────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    try:
        d["symbols"] = json.loads(d.get("symbols", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["symbols"] = []
    return d