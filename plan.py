"""Daglig planering av måltemperatur för värmepumpen utifrån spotpris och väder.

Torrkörning: skriptet räknar fram och loggar en plan men styr ingenting.
Endast standardbiblioteket används.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
PRICE_URL = "https://www.elprisetjustnu.se/api/v1/prices/{year}/{md}_{area}.json"
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}&hourly=temperature_2m"
    "&timezone={tz}&forecast_days=3"
)


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LLVP-heatpump-planner"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def hourly_prices(area, day, tz):
    """SEK/kWh per timme för ett dygn, eller {} om priserna inte är publicerade."""
    url = PRICE_URL.format(year=day.year, md=day.strftime("%m-%d"), area=area)
    try:
        rows = fetch_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise
    buckets = {}
    for row in rows:  # 24 timvärden eller 96 kvartsvärden
        start = datetime.fromisoformat(row["time_start"]).astimezone(tz)
        hour = start.replace(minute=0, second=0, microsecond=0)
        buckets.setdefault(hour, []).append(row["SEK_per_kWh"])
    return {h: sum(v) / len(v) for h, v in buckets.items()}


def hourly_temperatures(cfg, tz):
    url = WEATHER_URL.format(
        lat=cfg["latitude"], lon=cfg["longitude"], tz=cfg["timezone"].replace("/", "%2F")
    )
    data = fetch_json(url)["hourly"]
    return {
        datetime.fromisoformat(t).replace(tzinfo=tz): temp
        for t, temp in zip(data["time"], data["temperature_2m"])
    }


def percentile(values, pct):
    s = sorted(values)
    k = (len(s) - 1) * pct / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def round_half(x):
    return round(x * 2) / 2


def build_plan(prices, temps, cfg):
    """Returnerar en lista [{hour, price, outdoor_c, setpoint_c, reason}]."""
    hours = sorted(prices)
    if not hours:
        return []
    values = [prices[h] for h in hours]
    low = percentile(values, cfg["cheap_percentile"])
    high = percentile(values, cfg["expensive_percentile"])
    flat = (high - low) < cfg["min_spread_sek_per_kwh"]

    plan = []
    for h in hours:
        p = prices[h]
        outdoor = temps.get(h)
        setpoint, reason = cfg["base_c"], "grundtemperatur"
        if flat:
            reason = "små prisskillnader"
        elif p <= low:
            setpoint, reason = cfg["base_c"] + cfg["preheat_c"], "billig timme, förvärm"
        elif p >= high:
            if outdoor is not None and outdoor < cfg["no_setback_below_outdoor_c"]:
                reason = "dyr timme men för kallt ute för sänkning"
            else:
                setpoint, reason = cfg["base_c"] - cfg["setback_c"], "dyr timme, sänk"
        setpoint = round_half(min(max(setpoint, cfg["min_c"]), cfg["max_c"]))
        plan.append(
            {
                "hour": h.isoformat(),
                "price_sek_per_kwh": round(p, 3),
                "outdoor_c": None if outdoor is None else round(outdoor, 1),
                "setpoint_c": setpoint,
                "reason": reason,
            }
        )
    return plan


def to_schedule(plan):
    """Slår ihop på varandra följande timmar med samma måltemperatur."""
    blocks = []
    for row in plan:
        start = datetime.fromisoformat(row["hour"])
        if blocks and blocks[-1]["setpoint_c"] == row["setpoint_c"]:
            blocks[-1]["end"] = (start + timedelta(hours=1)).isoformat()
        else:
            blocks.append(
                {
                    "start": row["hour"],
                    "end": (start + timedelta(hours=1)).isoformat(),
                    "setpoint_c": row["setpoint_c"],
                }
            )
    return blocks


def render_markdown(now, plan, schedule):
    lines = [
        f"# Plan skapad {now:%Y-%m-%d %H:%M} (torrkörning, ingenting styrs)",
        "",
        "## Schema",
        "",
        "| Från | Till | Måltemp |",
        "|---|---|---|",
    ]
    for b in schedule:
        s, e = datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])
        lines.append(f"| {s:%a %d/%m %H:%M} | {e:%a %d/%m %H:%M} | {b['setpoint_c']} °C |")
    lines += ["", "## Timme för timme", "", "| Timme | Pris SEK/kWh | Ute °C | Måltemp | Skäl |", "|---|---|---|---|---|"]
    for r in plan:
        t = datetime.fromisoformat(r["hour"])
        out = "–" if r["outdoor_c"] is None else r["outdoor_c"]
        lines.append(
            f"| {t:%a %d/%m %H:%M} | {r['price_sek_per_kwh']} | {out} | {r['setpoint_c']} | {r['reason']} |"
        )
    return "\n".join(lines) + "\n"


def main(out_dir=ROOT / "plans"):
    cfg = json.loads((ROOT / "config.json").read_text())
    tz = ZoneInfo(cfg["timezone"])
    now = datetime.now(tz)
    this_hour = now.replace(minute=0, second=0, microsecond=0)

    prices = {}
    for offset in (0, 1):
        prices.update(hourly_prices(cfg["price_area"], (now + timedelta(days=offset)).date(), tz))
    end = this_hour + timedelta(hours=cfg["horizon_hours"])
    prices = {h: p for h, p in prices.items() if this_hour <= h < end}
    if not prices:
        sys.exit("Inga spotpriser hittades för perioden.")

    temps = hourly_temperatures(cfg, tz)
    plan = build_plan(prices, temps, cfg)
    schedule = to_schedule(plan)

    out_dir.mkdir(exist_ok=True)
    result = {"created": now.isoformat(), "dry_run": True, "schedule": schedule, "hours": plan}
    (out_dir / "latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    md = render_markdown(now, plan, schedule)
    (out_dir / "latest.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
