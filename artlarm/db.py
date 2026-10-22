"""SQLite-lagring: prenumerationer, fastigheter och skickade larm."""
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phone TEXT NOT NULL DEFAULT '',    -- tomt om bara e-post
  email TEXT NOT NULL DEFAULT '',    -- tomt om bara SMS
  start_date TEXT NOT NULL,          -- ISO-datum, kan ligga bakåt eller framåt i tiden
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS properties (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  geometry TEXT NOT NULL,            -- GeoJSON Polygon/MultiPolygon (WGS84)
  last_polled_at TEXT                -- NULL tills första (bakåtblickande) körningen gjorts
);
CREATE TABLE IF NOT EXISTS sent_alerts (
  property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  occurrence_id TEXT NOT NULL,
  sent_at TEXT NOT NULL,
  message TEXT,                      -- larmtexten, används i dygnssammanfattningen
  PRIMARY KEY (property_id, occurrence_id)
);
CREATE TABLE IF NOT EXISTS digests (
  email TEXT PRIMARY KEY,
  last_sent_at TEXT NOT NULL,        -- sammanfattningen täcker larm skickade efter detta
  last_date TEXT NOT NULL            -- svenskt datum då den senast skickades
);
"""


def split_emails(value: str) -> List[str]:
    """Prenumerationens e-postfält kan innehålla flera adresser, kommaseparerade."""
    return [e.strip() for e in (value or "").split(",") if e.strip()]


def add_email(con, sub_id: int, email: str) -> bool:
    """Lägger till en mottagare. Returnerar False om adressen redan finns."""
    row = con.execute("SELECT email FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
    current = split_emails(row["email"])
    if email.lower() in (e.lower() for e in current):
        return False
    con.execute("UPDATE subscriptions SET email = ? WHERE id = ?", (",".join(current + [email]), sub_id))
    con.commit()
    return True


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    if "message" not in {r["name"] for r in con.execute("PRAGMA table_info(sent_alerts)")}:
        con.execute("ALTER TABLE sent_alerts ADD COLUMN message TEXT")
    if "email" not in {r["name"] for r in con.execute("PRAGMA table_info(subscriptions)")}:
        con.execute("ALTER TABLE subscriptions ADD COLUMN email TEXT NOT NULL DEFAULT ''")
    return con


def add_subscription(con, phone: str, start_date: str, properties: List[Dict[str, Any]],
                     email: str = "") -> int:
    cur = con.execute(
        "INSERT INTO subscriptions (phone, email, start_date, created_at) VALUES (?, ?, ?, ?)",
        (phone, email, start_date, now_iso()),
    )
    sub_id = cur.lastrowid
    for p in properties:
        con.execute(
            "INSERT INTO properties (subscription_id, name, geometry) VALUES (?, ?, ?)",
            (sub_id, p["name"], json.dumps(p["geometry"])),
        )
    con.commit()
    return sub_id


def delete_subscription(con, sub_id: int) -> bool:
    cur = con.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
    con.commit()
    return cur.rowcount > 0


def get_subscription(con, sub_id: int) -> Optional[Dict[str, Any]]:
    row = con.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
    return _with_properties(con, row) if row else None


def list_subscriptions(con) -> List[Dict[str, Any]]:
    rows = con.execute("SELECT * FROM subscriptions ORDER BY id").fetchall()
    return [_with_properties(con, r) for r in rows]


def _with_properties(con, row) -> Dict[str, Any]:
    props = con.execute(
        "SELECT id, name, geometry, last_polled_at FROM properties WHERE subscription_id = ? ORDER BY id",
        (row["id"],),
    ).fetchall()
    return {
        "id": row["id"],
        "phone": row["phone"],
        "email": row["email"],
        "start_date": row["start_date"],
        "properties": [
            {"id": p["id"], "name": p["name"], "geometry": json.loads(p["geometry"]),
             "last_polled_at": p["last_polled_at"]} for p in props
        ],
    }


def set_polled(con, property_id: int) -> None:
    con.execute("UPDATE properties SET last_polled_at = ? WHERE id = ?", (now_iso(), property_id))
    con.commit()


def already_sent(con, property_id: int, occurrence_id: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sent_alerts WHERE property_id = ? AND occurrence_id = ?",
        (property_id, occurrence_id),
    ).fetchone() is not None


def mark_sent(con, property_id: int, occurrence_id: str, message: Optional[str] = None) -> None:
    con.execute(
        "INSERT OR IGNORE INTO sent_alerts (property_id, occurrence_id, sent_at, message) "
        "VALUES (?, ?, ?, ?)",
        (property_id, occurrence_id, now_iso(), message),
    )
    con.commit()
