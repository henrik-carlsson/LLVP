"""Kärnlogik: hitta nya observationer per fastighet och skicka larm."""
import logging
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

import config
import db
from notify import Notifier
from sos import Observation, SosClient

log = logging.getLogger("artlarm.poller")
STHLM = ZoneInfo("Europe/Stockholm")
_TO_SWEREF = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True).transform


def format_alert(obs: Observation, property_name: str) -> str:
    when = obs.observed_at
    when = when.replace(tzinfo=STHLM) if when.tzinfo is None else when.astimezone(STHLM)
    stamp = f"{when:%Y-%m-%d}" if (when.hour, when.minute) == (0, 0) else f"{when:%Y-%m-%d %H:%M}"  # 00:00 = ingen tid angiven
    parts = [f"{obs.taxon}, {stamp}, {property_name}"]
    if obs.location_note:
        parts[0] += f" [{obs.location_note}]"
    if obs.url:
        parts.append(obs.url)
    return ". ".join(parts)


def apply_location_accuracy(found: List[Observation], geometry: Dict[str, Any]) -> List[Observation]:
    """Behåller fynd inne i fastigheten, samt fynd utanför vars osäkerhetsradie når fastigheten
    (max MAX_UNCERTAINTY_M). De senare märks med `location_note`."""
    prop = transform(_TO_SWEREF, shape(geometry))
    out: List[Observation] = []
    for o in found:
        if o.lat is None or o.lon is None:
            out.append(o)  # SOS har redan matchat läget; saknas koordinater kan vi inte avgöra mer
            continue
        dist = prop.distance(transform(_TO_SWEREF, Point(o.lon, o.lat)))
        if dist == 0:
            out.append(o)
        elif o.uncertainty_m is not None and dist <= o.uncertainty_m <= config.MAX_UNCERTAINTY_M:
            note = f"OSÄKERT LÄGE: ca {round(dist)} m utanför fastigheten, osäkerhet ±{round(o.uncertainty_m)} m"
            out.append(replace(o, location_note=note))
    return out


def _local_date(dt: datetime) -> date:
    return dt.date() if dt.tzinfo is None else dt.astimezone(STHLM).date()


def poll_property(con, sos: SosClient, sender: Notifier, sub: Dict[str, Any],
                  prop: Dict[str, Any], today: Optional[date] = None) -> int:
    """Skickar larm för nya observationer. Returnerar antal observationer som larmats."""
    today = today or datetime.now(STHLM).date()
    start = date.fromisoformat(sub["start_date"])
    if start > today:
        return 0  # startdatum i framtiden: inget att hämta ännu

    first_run = prop["last_polled_at"] is None
    if first_run:
        found = sos.search(prop["geometry"], observed_from=start)  # bakåtblickande körning
    else:
        # modifiedDate är datumgranulärt; ta med gårdagen så inget missas vid dygnsskifte.
        found = sos.search(prop["geometry"], modified_from=today - timedelta(days=1))

    if config.CONSIDER_ACCURACY:
        found = apply_location_accuracy(found, prop["geometry"])

    new: List[Observation] = sorted(
        (o for o in found
         if _local_date(o.observed_at) >= start
         and not db.already_sent(con, prop["id"], o.occurrence_id)),
        key=lambda o: o.observed_at,
    )

    # Vid stora bakåtblickande mängder: de senaste enskilt, resten i ett sammanfattande SMS.
    overflow = new[:-config.MAX_SMS_PER_RUN] if len(new) > config.MAX_SMS_PER_RUN else []
    individual = new[len(overflow):]
    try:
        if overflow:
            sender.send(sub,
                        f"{len(overflow)} äldre artobservationer på {prop['name']} sedan "
                        f"{start} (enskilda larm skickas för de {len(individual)} senaste).",
                        f"Artlarm: äldre observationer – {prop['name']}")
            for o in overflow:
                db.mark_sent(con, prop["id"], o.occurrence_id)
        for o in individual:
            sender.send(sub, format_alert(o, prop["name"]), f"Artlarm{' (osäkert läge)' if o.location_note else ''}: {o.taxon} – {prop['name']}")
            db.mark_sent(con, prop["id"], o.occurrence_id)
    except Exception:
        log.exception("SMS-utskick misslyckades för fastighet %s; försöker igen nästa körning", prop["id"])
        return 0  # last_polled_at sätts inte → nästa körning gör om bakåtblicken, dedupen skyddar mot dubbletter

    db.set_polled(con, prop["id"])
    return len(new)


def poll_subscription(con, sos: SosClient, sender: Notifier, sub: Dict[str, Any],
                      today: Optional[date] = None) -> int:
    total = 0
    for prop in sub["properties"]:
        try:
            total += poll_property(con, sos, sender, sub, prop, today)
        except Exception:
            log.exception("Kunde inte polla fastighet %s", prop["id"])
    return total


def poll_all(con, sos: SosClient, sender: Notifier) -> int:
    return sum(poll_subscription(con, sos, sender, s) for s in db.list_subscriptions(con))
