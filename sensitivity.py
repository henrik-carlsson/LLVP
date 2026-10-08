"""Känslighetsanalys: hur påverkas besparingen av husparametrar och planinställningar?

Användning: python3 sensitivity.py 2026-01
Jämförelsen sker alltid mot konstant 14 °C i samma hus (samma husparametrar).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import simulate

ROOT = Path(__file__).parent


def evaluate(cfg, data):
    smart, const = simulate.run(cfg, data)
    ref = simulate.simulate(lambda h: 14.0, [r["hour"] for r in smart], data[2], data[3],
                            cfg["simulation"], 14.0)
    kr = sum(r["cost"] for r in smart)
    kr_ref = sum(r["cost"] for r in ref)
    return {
        "kwh": sum(r["kwh"] for r in smart),
        "kr": kr,
        "kr_ref": kr_ref,
        "save_kr": kr_ref - kr,
        "save_pct": (kr_ref - kr) / kr_ref * 100,
        "tmin": min(r["t_in"] for r in smart),
        "h_below_12": sum(1 for r in smart if r["t_in"] < 12.0),
    }


def variant(base, **changes):
    cfg = copy.deepcopy(base)
    for k, v in changes.items():
        (cfg["simulation"] if k in cfg["simulation"] else cfg)[k] = v
    return cfg


def table(title, rows):
    out = [f"## {title}", "", "| Variant | kWh | Kr smart | Kr konst 14 | Besparing kr | % | Min inne °C | Tim < 12 °C |",
           "|---|---|---|---|---|---|---|---|"]
    for label, r in rows:
        out.append(f"| {label} | {r['kwh']:.0f} | {r['kr']:.0f} | {r['kr_ref']:.0f} | {r['save_kr']:.0f} "
                   f"| {r['save_pct']:.1f} | {r['tmin']:.1f} | {r['h_below_12']} |")
    return "\n".join(out) + "\n"


def main(month):
    base = json.loads((ROOT / "config.json").read_text())
    data = simulate.load_data(base, month)
    ev = lambda **c: evaluate(variant(base, **c), data)
    parts = [f"# Känslighetsanalys {month}", "",
             "Smart plan jämförd med konstant 14 °C i samma hus. Basfall: UA 90 W/K, kapacitet 8 kWh/K, intervall 12–16 °C.", ""]

    parts.append(table("Grundfall", [("Basfall", ev())]))

    house = [(f"UA {ua} W/K, C {c} kWh/K", ev(ua_w_per_k=ua, capacity_kwh_per_k=c))
             for ua in (60, 90, 130) for c in (4, 8, 14)]
    parts.append(table("Hus: värmeförlust (UA) och värmekapacitet (C)", house))

    cop = [(f"COP vid 0 °C = {v}", ev(cop_at_0c=v)) for v in (2.6, 3.2, 3.8)]
    parts.append(table("Värmepumpens verkningsgrad", cop))

    pmax = [(f"Maxeffekt vid +7 °C = {v} kW", ev(pmax_kw_at_7c=v)) for v in (3.0, 4.0, 5.5)]
    parts.append(table("Värmepumpens maxeffekt", pmax))

    ranges = [
        ("12–16 °C (±2)", dict(min_c=12.0, max_c=16.0, preheat_c=2.0, setback_c=2.0)),
        ("12–18 °C (+4/−2)", dict(min_c=12.0, max_c=18.0, preheat_c=4.0, setback_c=2.0)),
        ("10–16 °C (+2/−4)", dict(min_c=10.0, max_c=16.0, preheat_c=2.0, setback_c=4.0)),
        ("10–18 °C (±4)", dict(min_c=10.0, max_c=18.0, preheat_c=4.0, setback_c=4.0)),
        ("10–20 °C (+6/−4)", dict(min_c=10.0, max_c=20.0, preheat_c=6.0, setback_c=4.0)),
        ("13–15 °C (±1)", dict(min_c=13.0, max_c=15.0, preheat_c=1.0, setback_c=1.0)),
    ]
    parts.append(table("Temperaturintervall (grund 14 °C)", [(l, ev(**c)) for l, c in ranges]))

    pct = [(f"billig ≤ P{lo}, dyr ≥ P{hi}", ev(cheap_percentile=lo, expensive_percentile=hi))
           for lo, hi in ((10, 90), (25, 75), (33, 67), (50, 50))]
    parts.append(table("Percentilgränser för billig/dyr timme", pct))

    spread = [(f"min prisspridning {v} kr/kWh", ev(min_spread_sek_per_kwh=v)) for v in (0.0, 0.10, 0.30)]
    parts.append(table("Prisspridning som krävs för att agera", spread))

    out = ROOT / "sim" / f"{month}-sensitivity.md"
    out.write_text("\n".join(parts))
    print("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-01")
