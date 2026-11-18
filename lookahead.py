"""Utvärderar förvärmning inför kalla perioder (längre prognoshorisont, högre max).

Användning: python3 lookahead.py 2026-01
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import simulate
from sensitivity import evaluate, table, variant

ROOT = Path(__file__).parent


def main(month):
    base = json.loads((ROOT / "config.json").read_text())
    data = simulate.load_data(base, month)
    ev = lambda **c: evaluate(variant(base, **c), data)
    cold = dict(max_c=20.0, precold_preheat_c=6.0, cold_trigger_c=-8.0, precold_mode="all")
    noisy = dict(forecast_sd_base_k=1.0, forecast_sd_per_hour_k=0.05)

    parts = [f"# Förvärmning inför kyla, {month}", "",
             "Jämförelse mot konstant 14 °C. Prognosen i simuleringen är antingen perfekt (facit) eller "
             "har ett samlat fel som växer med ledtiden (±1 K + 0,05 K/timme, dvs ca ±3,4 K vid 48 h; 1 sigma).", ""]

    parts.append(table("Utgångsläge och horisont (max 20 °C, +6 °C inför kyla, kyla = under −8 °C)", [
        ("Utan framförhållning (max 16)", ev()),
        ("Horisont 24 h", ev(lookahead_hours=24, **cold)),
        ("Horisont 48 h", ev(lookahead_hours=48, **cold)),
        ("Horisont 72 h", ev(lookahead_hours=72, **cold)),
        ("Horisont 96 h", ev(lookahead_hours=96, **cold)),
    ]))
    parts.append(table("Med osäker prognos (48 h)", [
        ("Perfekt prognos", ev(lookahead_hours=48, **cold)),
        ("Osäker prognos", ev(lookahead_hours=48, **cold, **noisy)),
        ("Osäker, horisont 72 h", ev(lookahead_hours=72, **cold, **noisy)),
    ]))
    parts.append(table("Hur högt (48 h, perfekt prognos)", [
        (f"Max {m} °C (+{m-14})", ev(lookahead_hours=48, **{**cold, "max_c": float(m), "precold_preheat_c": float(m - 14)}))
        for m in (16, 18, 20, 22, 24)
    ]))
    parts.append(table("Vad räknas som kyla (48 h, max 20)", [
        (f"Under {t} °C", ev(lookahead_hours=48, **{**cold, "cold_trigger_c": float(t)}))
        for t in (-5, -8, -10, -12)
    ]))
    parts.append(table("Förvärm hela vägen eller bara billiga timmar (48 h, max 20)", [
        ("Alla icke-dyra timmar", ev(lookahead_hours=48, **cold)),
        ("Bara billiga timmar", ev(lookahead_hours=48, **{**cold, "precold_mode": "cheap"})),
    ]))
    parts.append(table("Samma sak i ett sämre hus (UA 130 W/K, C 8) och svagare pump (3,0 kW)", [
        ("UA 130, utan framförhållning", ev(ua_w_per_k=130)),
        ("UA 130, 48 h, max 20", ev(ua_w_per_k=130, lookahead_hours=48, **cold)),
        ("Pump 3 kW, utan framförhållning", ev(pmax_kw_at_7c=3.0)),
        ("Pump 3 kW, 48 h, max 20", ev(pmax_kw_at_7c=3.0, lookahead_hours=48, **cold)),
    ]))
    out = ROOT / "sim" / f"{month}-lookahead.md"
    out.write_text("\n".join(parts))
    print("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-01")
