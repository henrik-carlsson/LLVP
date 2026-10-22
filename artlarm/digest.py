"""Dygnssammanfattning: ett mejl per e-postadress, även när inget registrerats."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

import config
import db
from email_sender import EmailSender
from poller import RUN_LOCK, STHLM

log = logging.getLogger("artlarm.digest")


def _local(iso: str) -> datetime:
    return datetime.fromisoformat(iso).astimezone(STHLM)


def build_digest(con, email: str, since_iso: str, now: datetime):
    """Returnerar (ämne, brödtext) för en e-postadress, över alla dess fastigheter."""
    props = con.execute(
        "SELECT p.id, p.name FROM properties p JOIN subscriptions s ON s.id = p.subscription_id "
        "WHERE s.email = ? ORDER BY p.name", (email,)).fetchall()
    alerts = con.execute(
        "SELECT a.property_id, a.message FROM sent_alerts a "
        "JOIN properties p ON p.id = a.property_id JOIN subscriptions s ON s.id = p.subscription_id "
        "WHERE s.email = ? AND a.sent_at > ? ORDER BY a.sent_at", (email, since_iso)).fetchall()
    by_prop: Dict[int, List[str]] = {}
    for a in alerts:
        by_prop.setdefault(a["property_id"], []).append(a["message"] or "(larmtext saknas)")

    n = len(alerts)
    subject = (f"Artlarm: dygnssammanfattning {now.astimezone(STHLM):%Y-%m-%d} – "
               + (f"{n} nya observationer" if n != 1 else "1 ny observation") if n
               else f"Artlarm: dygnssammanfattning {now.astimezone(STHLM):%Y-%m-%d} – inga nya observationer")
    lines = [f"Sammanfattning av larm sedan {_local(since_iso):%Y-%m-%d %H:%M}.", ""]
    for p in props:
        items = by_prop.get(p["id"], [])
        lines.append(f"{p['name']}: " + (f"{len(items)} nya" if items else "inga nya observationer"))
        lines += [f"  - {m}" for m in items]
        lines.append("")
    return subject, "\n".join(lines).rstrip() + "\n"


def send_due_digests(con, email_sender: EmailSender, now: Optional[datetime] = None,
                     before_send: Optional[Callable[[], None]] = None) -> int:
    """Skickar sammanfattning till varje adress som inte fått någon idag, efter kl DIGEST_HOUR.
    En adress som ses för första gången 'seedas' och får sin första sammanfattning nästa dag."""
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(STHLM)
    today = local.date().isoformat()
    sent = 0
    with RUN_LOCK:
        emails = [r["email"] for r in con.execute(
            "SELECT DISTINCT email FROM subscriptions WHERE email != '' ORDER BY email")]
        due = []
        for email in emails:
            row = con.execute("SELECT * FROM digests WHERE email = ?", (email,)).fetchone()
            if row is None:  # första gången: sammanfattningen börjar täcka senaste dygnet
                con.execute("INSERT INTO digests (email, last_sent_at, last_date) VALUES (?, ?, ?)",
                            (email, (now - timedelta(hours=24)).isoformat(timespec="seconds"), today))
                con.commit()
            elif row["last_date"] != today and local.hour >= config.DIGEST_HOUR:
                due.append((email, row["last_sent_at"]))
        if due and before_send:
            try:
                before_send()  # hämta det senaste innan sammanfattningen
            except Exception:
                log.exception("Pollning före sammanfattning misslyckades")
        for email, since in due:
            try:
                subject, body = build_digest(con, email, since, now)
                email_sender.send(email, subject, body)
            except Exception:
                log.exception("Sammanfattning till %s misslyckades; försöker igen", email)
                continue
            con.execute("UPDATE digests SET last_sent_at = ?, last_date = ? WHERE email = ?",
                        (now.isoformat(timespec="seconds"), today, email))
            con.commit()
            sent += 1
    return sent
