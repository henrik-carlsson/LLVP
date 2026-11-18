"""Pris per timme på dygnet (max/min/medel över månadens dygn). Användning: python3 hourly_stats.py 2026-01"""
import csv
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

month = sys.argv[1] if len(sys.argv) > 1 else "2026-01"
root = Path(__file__).parent / "sim"
by_hour = {h: [] for h in range(24)}
days = set()
for r in csv.DictReader(open(root / f"{month}-hourly.csv")):
    t = datetime.fromisoformat(r["timme"])
    by_hour[t.hour].append(float(r["pris_sek_kwh"]))
    days.add(t.date())

stats = {h: (max(v), min(v), sum(v) / len(v)) for h, v in by_hour.items()}
with open(root / f"{month}-price-by-hour.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timme", "max_kr_kwh", "min_kr_kwh", "medel_kr_kwh"])
    for h, (mx, mn, av) in stats.items():
        w.writerow([h, round(mx, 3), round(mn, 3), round(av, 3)])

hrs = list(range(24))
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.fill_between(hrs, [stats[h][1] for h in hrs], [stats[h][0] for h in hrs], color="#2563eb", alpha=0.12, label="Spann min–max")
ax.plot(hrs, [stats[h][0] for h in hrs], color="#dc2626", marker="o", ms=3, lw=1.3, label="Högsta")
ax.plot(hrs, [stats[h][2] for h in hrs], color="#2563eb", marker="o", ms=3, lw=2, label="Medel")
ax.plot(hrs, [stats[h][1] for h in hrs], color="#16a34a", marker="o", ms=3, lw=1.3, label="Lägsta")
ax.set_xticks(hrs); ax.set_xlabel("Timme på dygnet (start, svensk tid)"); ax.set_ylabel("Spotpris SE3, kr/kWh")
ax.set_title(f"Timpris per klockslag, {month} ({len(days)} dygn)"); ax.grid(alpha=0.25); ax.legend(ncol=4, loc="upper left")
fig.tight_layout(); fig.savefig(root / f"{month}-price-by-hour.png", dpi=110)

allp = [p for v in by_hour.values() for p in v]
print(f"dygn={len(days)} max={max(allp):.3f} min={min(allp):.3f} medel={sum(allp)/len(allp):.3f}")
print("timme  max    min    medel")
for h, (mx, mn, av) in stats.items():
    print(f"{h:02d}   {mx:6.3f} {mn:6.3f} {av:6.3f}")
