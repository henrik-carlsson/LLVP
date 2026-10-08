"""Simulerar planeraren mot historiska priser/väder och jämför med konstant måltemperatur.

Användning: python3 simulate.py 2026-01
Husmodellen är en enkel envärmemassa-modell med antagna parametrar (config.json, "simulation").
Resultatet är en indikation; jämförelsen mellan strategierna är mer pålitlig än absolutnivåerna.
"""
from __future__ import annotations

import calendar
import csv
import json
import sys
import urllib.parse
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import plan

ROOT = Path(__file__).parent
ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
    "&start_date={s}&end_date={e}&hourly=temperature_2m&timezone={tz}"
)
RUN_HOUR = 13  # planeraren körs ca 13:30 svensk vintertid


def historical_temperatures(cfg, tz, start, end):
    url = ARCHIVE_URL.format(
        lat=cfg["latitude"], lon=cfg["longitude"], s=start, e=end,
        tz=urllib.parse.quote(cfg["timezone"], safe=""),
    )
    data = plan.fetch_json(url)["hourly"]
    return {
        datetime.fromisoformat(t).replace(tzinfo=tz): v
        for t, v in zip(data["time"], data["temperature_2m"])
    }


def cop(outdoor, sim):
    return min(max(sim["cop_at_0c"] + sim["cop_per_k"] * outdoor, sim["cop_min"]), sim["cop_max"])


def pmax_kw(outdoor, sim):
    return max(sim["pmax_kw_at_7c"] + sim["pmax_derate_kw_per_k"] * (outdoor - 7), 0.5)


def step_house(t_in, t_out, setpoint, sim):
    """En timme. Pumpen strävar efter att nå måltemperaturen vid timmens slut."""
    ua = sim["ua_w_per_k"] / 1000  # kW/K
    cap = sim["capacity_kwh_per_k"]  # kWh/K
    want = cap * (setpoint - t_in) + ua * (t_in - t_out)
    heat = min(max(want, 0.0), pmax_kw(t_out, sim))  # kWh termiskt under timmen
    t_next = t_in + (heat - ua * (t_in - t_out)) / cap
    return t_next, heat, heat / cop(t_out, sim)


def planned_setpoints(cfg, tz, prices_all, temps, first_day, last_day):
    """Rullande plan: varje dags körning gäller tills nästa körning tar över."""
    setpoints = {}
    day = first_day - timedelta(days=1)
    while day <= last_day:
        run = datetime(day.year, day.month, day.day, RUN_HOUR, tzinfo=tz)
        end = run + timedelta(hours=cfg["horizon_hours"])
        window = {h: p for h, p in prices_all.items() if run <= h < end}
        rows = plan.build_plan(window, temps, cfg)
        next_run = run + timedelta(days=1)
        for r in rows:
            h = datetime.fromisoformat(r["hour"])
            if run <= h < next_run:
                setpoints[h] = r["setpoint_c"]
        day += timedelta(days=1)
    return setpoints


def simulate(setpoint_of, hours, prices, temps, sim, t0):
    t_in, rows = t0, []
    for h in hours:
        sp = setpoint_of(h)
        t_next, heat, kwh = step_house(t_in, temps[h], sp, sim)
        rows.append({"hour": h, "setpoint": sp, "t_out": temps[h], "t_in": t_in,
                     "kwh": kwh, "cost": kwh * prices[h], "price": prices[h]})
        t_in = t_next
    return rows


def load_data(cfg, month):
    year, mon = map(int, month.split("-"))
    tz = ZoneInfo(cfg["timezone"])
    first, last = date(year, mon, 1), date(year, mon, calendar.monthrange(year, mon)[1])

    prices_all = {}
    d = first - timedelta(days=1)
    while d <= last + timedelta(days=1):
        prices_all.update(plan.hourly_prices(cfg["price_area"], d, tz))
        d += timedelta(days=1)
    temps = historical_temperatures(cfg, tz, first - timedelta(days=1), last + timedelta(days=1))
    return first, last, prices_all, temps


def run(cfg, data):
    first, last, prices_all, temps = data
    sim = cfg["simulation"]
    tz = ZoneInfo(cfg["timezone"])
    start = datetime(first.year, first.month, first.day, tzinfo=tz)
    hours = []
    h = start
    while h.date() <= last:
        hours.append(h)
        h += timedelta(hours=1)
    # fasta (UTC-baserade) timsteg så att sommar/vintertid inte ger luckor
    hours = [datetime.fromtimestamp(start.timestamp() + 3600 * i, tz) for i in range(len(hours))]

    sp_plan = planned_setpoints(cfg, tz, prices_all, temps, first, last)
    smart = simulate(lambda h: sp_plan[h], hours, prices_all, temps, sim, cfg["base_c"])
    const = simulate(lambda h: cfg["base_c"], hours, prices_all, temps, sim, cfg["base_c"])
    return smart, const


def main(month):
    cfg = json.loads((ROOT / "config.json").read_text())
    data = load_data(cfg, month)
    smart, const = run(cfg, data)
    return cfg, data[0], data[1], smart, const


def daily(rows):
    out = {}
    for r in rows:
        d = out.setdefault(r["hour"].date(), {"kwh": 0.0, "cost": 0.0, "sp": [], "tin": [], "tout": []})
        d["kwh"] += r["kwh"]; d["cost"] += r["cost"]
        d["sp"].append(r["setpoint"]); d["tin"].append(r["t_in"]); d["tout"].append(r["t_out"])
    return out


def write_outputs(month, cfg, smart, const):
    out = ROOT / "sim"
    out.mkdir(exist_ok=True)
    with open(out / f"{month}-hourly.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timme", "ute_c", "pris_sek_kwh", "mal_smart", "inne_smart", "kwh_smart",
                    "kr_smart", "mal_konstant", "inne_konstant", "kwh_konstant", "kr_konstant"])
        for a, b in zip(smart, const):
            w.writerow([a["hour"].isoformat(), round(a["t_out"], 1), round(a["price"], 3),
                        a["setpoint"], round(a["t_in"], 2), round(a["kwh"], 3), round(a["cost"], 3),
                        b["setpoint"], round(b["t_in"], 2), round(b["kwh"], 3), round(b["cost"], 3)])

    ds, dc = daily(smart), daily(const)
    lines = [f"# Simulering {month}", "",
             "Antagen husmodell: " + ", ".join(f"{k}={v}" for k, v in cfg["simulation"].items()), "",
             "| Dag | Ute °C (snitt) | Mål smart (min–max) | Inne smart (min) | kWh smart | kr smart | Ack kr smart "
             "| Inne konst (min) | kWh konst | kr konst | Ack kr konst |", "|" + "---|" * 11]
    acc_s = acc_c = 0.0
    for day in ds:
        s, c = ds[day], dc[day]
        acc_s += s["cost"]; acc_c += c["cost"]
        lines.append(
            f"| {day:%d/%m} | {sum(s['tout'])/24:.1f} | {min(s['sp']):g}–{max(s['sp']):g} | {min(s['tin']):.1f} "
            f"| {s['kwh']:.1f} | {s['cost']:.1f} | {acc_s:.0f} | {min(c['tin']):.1f} | {c['kwh']:.1f} "
            f"| {c['cost']:.1f} | {acc_c:.0f} |")
    tk_s, tk_c = sum(r["kwh"] for r in smart), sum(r["kwh"] for r in const)
    lines += ["", f"**Totalt:** smart {tk_s:.0f} kWh / {acc_s:.0f} kr, konstant 14 °C {tk_c:.0f} kWh / {acc_c:.0f} kr. "
              f"Skillnad {acc_c - acc_s:.0f} kr ({(acc_c - acc_s) / acc_c * 100:.0f} %). "
              f"Snittpris smart {acc_s / tk_s:.2f} kr/kWh, konstant {acc_c / tk_c:.2f} kr/kWh.",
              "", "Kostnaden avser enbart spotpris (exkl. påslag, nätavgift, skatt, moms)."]
    (out / f"{month}.md").write_text("\n".join(lines) + "\n")
    return acc_s, acc_c, tk_s, tk_c


if __name__ == "__main__":
    month = sys.argv[1] if len(sys.argv) > 1 else "2026-01"
    cfg, first, last, smart, const = main(month)
    print(write_outputs(month, cfg, smart, const))
