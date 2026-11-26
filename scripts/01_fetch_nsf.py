"""Fetch NSF awards for youth-facing STEM education programs via the public NSF Award API.

Personal data is dropped at fetch time: only award, program, organization and location fields
are kept (no PI, co-PI or program officer names, emails or phones).

python3 -I scripts/01_fetch_nsf.py   -> data/raw/nsf/awards.jsonl (+ lock entry)
"""
import csv, datetime as dt, hashlib, json, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "nsf"; RAW.mkdir(parents=True, exist_ok=True)
API = "https://api.nsf.gov/services/v1/awards.json?"
# query token -> exact program-name substring that must appear in fundProgramName
PROGRAMS = {"ITEST": "ITEST", "AISL": "AISL", "DRK-12": "Discovery Research K-12", "CSforAll": "CSforAll",
            "INCLUDES": "INCLUDES", "STEM+C": "STEM + Computing"}
KEEP = ["id", "title", "abstractText", "fundProgramName", "program", "progRefCode", "dirAbbr", "divAbbr", "date", "startDate",
        "expDate", "fundsObligatedAmt", "estimatedTotalAmt", "transType", "cfdaNumber", "awardeeName", "awardeeStateCode",
        "awardeeZipCode", "perfLocation", "perfCity", "perfStateCode", "perfZipCode", "awdSpAttnDesc", "activeAwd"]
DATE_START, DATE_END = "01/01/2014", "12/31/2024"


def get(params, tries=5):
    for k in range(tries):
        try:
            with urllib.request.urlopen(API + urllib.parse.urlencode(params), timeout=120) as r:
                return json.load(r)["response"]
        except Exception as e:  # network hiccup: back off and retry
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


awards = {}
for token, exact in PROGRAMS.items():
    off, n = 1, None
    while True:
        d = get({"fundProgramName": token, "dateStart": DATE_START, "dateEnd": DATE_END, "rpp": 25, "offset": off})
        n = d.get("metadata", {}).get("totalCount", 0) if n is None else n
        batch = d.get("award", [])
        for a in batch:
            if exact.lower() in (a.get("fundProgramName") or "").lower():
                rec = awards.setdefault(a["id"], {k: a.get(k) for k in KEEP} | {"query_programs": []})
                rec["query_programs"].append(exact)
        off += 25
        if not batch or off > n:
            break
        time.sleep(0.3)
    print(f"{token}: {n} matched by API; running total of unique awards {len(awards)}")

out = RAW / "awards.jsonl"
with open(out, "w") as f:
    for a in sorted(awards.values(), key=lambda x: x["id"]):
        f.write(json.dumps(a) + "\n")
h = hashlib.sha256(out.read_bytes()).hexdigest()
lock_path = ROOT / "data" / "sources.lock.csv"
rows = list(csv.DictReader(open(lock_path))) if lock_path.exists() else []
rows = [r for r in rows if r["file"] != "nsf/awards.jsonl"]
rows.append({"file": "nsf/awards.jsonl", "url": API + f"fundProgramName=<{','.join(PROGRAMS)}>&dateStart={DATE_START}&dateEnd={DATE_END}",
             "downloaded_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(), "bytes": out.stat().st_size, "sha256": h})
fields = ["file", "url", "downloaded_utc", "bytes", "sha256"]
with open(lock_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print(f"wrote {out} ({len(awards)} awards)")
