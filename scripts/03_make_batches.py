"""Build agent input batches.

python3 -I scripts/03_make_batches.py
  -> data/interim/batches/nsf/batch_NNNN.jsonl   (40 awards each, sorted by award id)
  -> data/interim/batches/ojjdp/batch_NNNN.jsonl (50 grants each)
  -> data/coded/nsf_reliability_batches.txt      (fixed sample of 8 NSF batches for a second, reference-model pass)
"""
import json, random
from pathlib import Path
import re

_CONTACT = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")


def redact(text):
    """Remove email addresses and phone numbers that sometimes appear in award text."""
    return _CONTACT.sub("[redacted]", text) if isinstance(text, str) else text


ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "data" / "interim" / "batches"
SEED = 20261119


def write(kind, recs, size):
    d = B / kind; d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("batch_*.jsonl"):
        f.unlink()
    n = 0
    for k in range(0, len(recs), size):
        n += 1
        with open(d / f"batch_{n:04d}.jsonl", "w") as fh:
            for r in recs[k:k + size]:
                fh.write(json.dumps(r) + "\n")
    return n


nsf = [json.loads(l) for l in open(ROOT / "data" / "raw" / "nsf" / "awards.jsonl")]
nsf_recs = [{"id": a["id"], "title": a["title"], "abstract": redact(a["abstractText"] or ""), "program": a["fundProgramName"],
             "state": a["perfStateCode"], "city": a["perfCity"], "organization": a["awardeeName"]} for a in sorted(nsf, key=lambda x: x["id"])]
n_nsf = write("nsf", nsf_recs, 40)

oj = [json.loads(l) for l in open(ROOT / "data" / "raw" / "usaspending" / "mentoring_awards.jsonl")]
oj_recs = [{"id": a["generated_internal_id"], "title": redact(a["Description"] or ""), "abstract": "", "organization": a["Recipient Name"],
            "state": a["Place of Performance State Code"], "amount": a["Award Amount"], "start": a["Start Date"]}
           for a in sorted(oj, key=lambda x: x["generated_internal_id"])]
n_oj = write("ojjdp", oj_recs, 50)

rel = sorted(random.Random(SEED).sample(range(1, n_nsf + 1), 8))
C = ROOT / "data" / "coded"; C.mkdir(parents=True, exist_ok=True)
(C / "nsf_reliability_batches.txt").write_text("\n".join(f"batch_{i:04d}" for i in rel) + "\n")
print(f"NSF: {len(nsf_recs)} awards in {n_nsf} batches; OJJDP: {len(oj_recs)} grants in {n_oj} batches; reliability batches {rel}")
