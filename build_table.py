"""Write battle_table.json for 1..10 x 1..10 and chart a sample of 10 into eda_charts/."""
import json
import os

from risk_chains import plot_summary, summarize

N = 10
SAMPLE = [(1, 1), (2, 2), (3, 3), (5, 5), (10, 10),   # diagonal
          (5, 2), (10, 3), (7, 4),                     # attacker-heavy
          (2, 5), (3, 10)]                             # defender-heavy
OUTDIR = "eda_charts"

table = [summarize(i, j) for i in range(1, N + 1) for j in range(1, N + 1)]
with open("battle_table.json", "w") as f:
    json.dump(table, f, indent=2)

by_key = {(r["i"], r["j"]): r for r in table}
os.makedirs(OUTDIR, exist_ok=True)
for i, j in SAMPLE:
    plot_summary(by_key[(i, j)], os.path.join(OUTDIR, f"battle_{i}v{j}.pdf"))
print(f"battle_table.json: {len(table)} entries; {len(SAMPLE)} charts -> {OUTDIR}/")