"""Pipeline progress and pending batches. A batch is done when its output exists AND validates.

python3 -I scripts/status.py [--json]
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B, C = ROOT / "data" / "interim" / "batches", ROOT / "data" / "coded"


def valid(kind, out):
    return out.exists() and subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "validate.py"), kind, str(out)],
                                           capture_output=True).returncode == 0


def pending(kind, out_dir, only=None):
    bs = [b.stem for b in sorted((B / kind).glob("batch_*.jsonl"))]
    if only is not None:
        bs = [b for b in bs if b in only]
    return [b for b in bs if not valid(kind, out_dir / f"{b}.json")], len(bs)


rel = set((C / "nsf_reliability_batches.txt").read_text().split()) if (C / "nsf_reliability_batches.txt").exists() else set()
s = {}
s["nsf_main_pending"], s["nsf_main_total"] = pending("nsf", C / "nsf" / "main")
s["nsf_reference_pending"], s["nsf_reference_total"] = pending("nsf", C / "nsf" / "reference", rel)
s["ojjdp_pending"], s["ojjdp_total"] = pending("ojjdp", C / "ojjdp")
if "--json" in sys.argv:
    print(json.dumps(s))
else:
    for k in ("nsf_main", "nsf_reference", "ojjdp"):
        print(f"{k:14s} {s[k + '_total'] - len(s[k + '_pending'])}/{s[k + '_total']} batches done")
