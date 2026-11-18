"""Teoretiskt tak: optimal styrning med perfekt kännedom om hela månadens pris och väder.

Dynamisk programmering över inomhustemperatur och pumpeffekt, med samma husmodell som simuleringen.
Det är ingen realistisk strategi (ingen känner hela månaden i förväg) utan en övre gräns för
vad förvärmning inom ett temperaturband kan ge.

Användning: python3 ceiling.py 2026-01
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import simulate

ROOT = Path(__file__).parent


def optimal_cost(cfg, hours, prices, temps, lo, hi, t_start=14.0, end_penalty=3.0, low_penalty=50.0):
    sim = cfg["simulation"]
    ua, cap = sim["ua_w_per_k"] / 1000, sim["capacity_kwh_per_k"]
    grid = np.arange(lo - 3.0, hi + 0.001, 0.1)
    value = end_penalty * np.maximum(t_start - grid, 0)  # måste sluta vid ca startnivån
    kwh_total = 0.0
    for h in reversed(hours):
        t_out, price = temps[h], prices[h]
        q = np.linspace(0, simulate.pmax_kw(t_out, sim), 41)  # termiska kWh under timmen
        c = simulate.cop(t_out, sim)
        nxt = grid[:, None] + (q[None, :] - ua * (grid[:, None] - t_out)) / cap
        nxt_c = np.clip(nxt, grid[0], grid[-1])
        cont = np.interp(nxt_c, grid, value)
        stage = q[None, :] / c * price
        pen = low_penalty * np.maximum(lo - nxt, 0) + 1e3 * np.maximum(nxt - hi, 0)
        value = (stage + cont + pen).min(axis=1)
    return float(np.interp(t_start, grid, value))


def main(month):
    cfg = json.loads((ROOT / "config.json").read_text())
    data = simulate.load_data(cfg, month)
    first, last, prices, temps = data
    smart, const = simulate.run(cfg, data)
    hours = [r["hour"] for r in const]
    kr_const = sum(r["cost"] for r in const)
    rows = [("Konstant 14 °C", kr_const), ("Planerare (33/67, 12–16 °C)", sum(r["cost"] for r in smart))]
    for c_ in (13.0, 12.0, 10.0):
        ref = simulate.simulate(lambda h, c_=c_: c_, hours, prices, temps, cfg["simulation"], 14.0)
        rows.append((f"Konstant {c_:g} °C (för jämförelse)", sum(r["cost"] for r in ref)))
    for lo, hi in ((12, 16), (12, 20), (10, 20), (13, 15), (14, 20)):
        rows.append((f"Optimalt, band {lo}–{hi:g} °C", optimal_cost(cfg, hours, prices, temps, lo, hi)))
    lines = [f"# Teoretiskt tak {month}", "",
             "Optimal styrning med perfekt framförhållning över hela månaden (DP, samma husmodell).", "",
             "| Strategi | Kr (spot) | Besparing mot konstant 14 | % |", "|---|---|---|---|"]
    for label, kr in rows:
        lines.append(f"| {label} | {kr:.0f} | {kr_const - kr:.0f} | {(kr_const - kr) / kr_const * 100:.1f} |")
    out = "\n".join(lines) + "\n"
    (ROOT / "sim" / f"{month}-ceiling.md").write_text(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-01")
