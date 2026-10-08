"""Ritar diagram av simuleringen (läser sim/<månad>-hourly.csv)."""
import csv
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

month = sys.argv[1] if len(sys.argv) > 1 else "2026-01"
rows = list(csv.DictReader(open(Path(__file__).parent / "sim" / f"{month}-hourly.csv")))
t = [datetime.fromisoformat(r["timme"]).replace(tzinfo=None) for r in rows]
f = lambda k: [float(r[k]) for r in rows]
acc = lambda k: [sum(f(k)[: i + 1]) for i in range(len(rows))]

fig, ax = plt.subplots(4, 1, figsize=(13, 13), sharex=True)
ax[0].plot(t, f("ute_c"), color="#6b7280", lw=0.8); ax[0].set_ylabel("Utetemp °C")
ax[1].step(t, f("mal_smart"), color="#2563eb", lw=0.9, where="post", label="Måltemp smart")
ax[1].plot(t, f("inne_smart"), color="#dc2626", lw=1.2, label="Inne smart (uppskattad)")
ax[1].plot(t, f("inne_konstant"), color="#6b7280", lw=1.0, ls="--", label="Inne konstant 14 °C")
ax[1].set_ylabel("°C"); ax[1].legend(ncol=3, loc="lower left")
ax[2].plot(t, f("pris_sek_kwh"), color="#d97706", lw=0.8); ax[2].set_ylabel("Spotpris kr/kWh")
ax[3].plot(t, acc("kr_smart"), color="#2563eb", label="Smart"); ax[3].plot(t, acc("kr_konstant"), color="#6b7280", ls="--", label="Konstant 14 °C")
ax[3].set_ylabel("Ackumulerad kostnad kr"); ax[3].legend()
for a in ax: a.grid(alpha=0.25)
fig.suptitle(f"Simulering {month}: smart plan mot konstant 14 °C", y=0.995)
fig.tight_layout()
fig.savefig(Path(__file__).parent / "sim" / f"{month}.png", dpi=110)
