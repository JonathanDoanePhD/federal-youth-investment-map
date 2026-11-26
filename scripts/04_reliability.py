"""Agreement between the main tagging pass (Sonnet) and the reference pass (default model)
on the fixed reliability batches.

python3 -I scripts/04_reliability.py -> output/tagging_reliability.csv
Single-choice fields: percent agreement and Cohen's kappa. List fields: per-label kappa
(label present vs absent) and mean Jaccard overlap.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "coded" / "nsf"
SINGLE = ["serves_youth", "grade_band", "mentoring", "bridging", "ai_cs", "setting", "evaluation", "service_geography"]
LISTS = ["audience", "models", "targets"]


def kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = (a == b).mean(); cats = np.union1d(a, b)
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def load(p):
    return {str(e["id"]): e for f in sorted((C / p).glob("batch_*.json")) for e in json.loads(f.read_text())}


M, R = load("main"), load("reference")
ids = sorted(set(M) & set(R))
rows = []
for f in SINGLE:
    a = [str(M[i][f]) for i in ids]; b = [str(R[i][f]) for i in ids]
    rows.append({"field": f, "n": len(ids), "pct_agree": np.mean([x == y for x, y in zip(a, b)]), "kappa": kappa(a, b)})
# Evaluation is defined for youth outcomes: harmonize "no youth served" to none_stated in both passes,
# then compare (the main and reference passes applied that rule differently in the pilot).
yo = [i for i in ids if M[i]["serves_youth"] != "none" and R[i]["serves_youth"] != "none"]
a = [M[i]["evaluation"] for i in yo]; b = [R[i]["evaluation"] for i in yo]
rows.append({"field": "evaluation (both say youth served)", "n": len(yo), "pct_agree": np.mean([x == y for x, y in zip(a, b)]) if yo else np.nan,
             "kappa": kappa(a, b) if yo else np.nan})
a = [str(M[i]["evaluation"] in ("rct", "quasi_experimental")) for i in yo]; b = [str(R[i]["evaluation"] in ("rct", "quasi_experimental")) for i in yo]
rows.append({"field": "evaluation rigorous (rct/quasi) yes-no, youth served", "n": len(yo), "pct_agree": np.mean([x == y for x, y in zip(a, b)]) if yo else np.nan,
             "kappa": kappa(a, b) if yo else np.nan})
for f in LISTS:
    jac = [len(set(M[i][f]) & set(R[i][f])) / max(1, len(set(M[i][f]) | set(R[i][f]))) for i in ids]
    rows.append({"field": f"{f} (mean Jaccard)", "n": len(ids), "pct_agree": np.mean(jac), "kappa": np.nan})
    for lab in sorted({x for i in ids for x in M[i][f] + R[i][f]}):
        a = [lab in M[i][f] for i in ids]; b = [lab in R[i][f] for i in ids]
        if sum(a) + sum(b) >= 5:
            rows.append({"field": f"{f}:{lab}", "n": len(ids), "pct_agree": np.mean([x == y for x, y in zip(a, b)]), "kappa": kappa(a, b)})
yr = [(M[i]["youth_reach"], R[i]["youth_reach"]) for i in ids]
rows.append({"field": "youth_reach (same value or both null)", "n": len(ids), "pct_agree": np.mean([x == y for x, y in yr]), "kappa": np.nan})
out = pd.DataFrame(rows)
(ROOT / "output").mkdir(exist_ok=True)
out.to_csv(ROOT / "output" / "tagging_reliability.csv", index=False, float_format="%.3f")
print(out.round(2).to_string(index=False))
