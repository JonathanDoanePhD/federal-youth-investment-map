"""Fetch federal youth mentoring and college-access grants from the public USAspending API.

- County totals (place of performance) by fiscal year for four Assistance Listings.
- Award-level records (with short descriptions) for 16.726 Juvenile Mentoring, for agent tagging.
Recipient organizations only; email addresses and phone numbers in descriptions are redacted at fetch.

python3 -I scripts/02_fetch_usaspending.py -> data/raw/usaspending/{county_totals.csv, mentoring_awards.jsonl}
"""
import csv, datetime as dt, hashlib, json, time, urllib.request
from pathlib import Path
import re

_CONTACT = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")


def redact(text):
    """Remove email addresses and phone numbers that sometimes appear in award text."""
    return _CONTACT.sub("[redacted]", text) if isinstance(text, str) else text


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "usaspending"; RAW.mkdir(parents=True, exist_ok=True)
API = "https://api.usaspending.gov/api/v2"
PROGRAMS = {"16.726": "OJJDP Juvenile Mentoring", "84.334": "GEAR UP", "84.047": "Upward Bound", "84.044": "Talent Search"}
FYS = range(2015, 2025)


def post(path, body, tries=5):
    for k in range(tries):
        try:
            req = urllib.request.Request(API + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


rows = []
for cfda, name in PROGRAMS.items():
    for fy in FYS:
        tp = [{"start_date": f"{fy - 1}-10-01", "end_date": f"{fy}-09-30"}]
        d = post("/search/spending_by_geography/", {"scope": "place_of_performance", "geo_layer": "county",
                                                    "filters": {"program_numbers": [cfda], "time_period": tp}})
        for r in d["results"]:
            rows.append({"cfda": cfda, "program": name, "fy": fy, "county_fips": r["shape_code"], "county_name": r["display_name"],
                         "amount": r["aggregated_amount"]})
        time.sleep(0.3)
    print(cfda, name, "rows so far", len(rows))
ct = RAW / "county_totals.csv"
with open(ct, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

FIELDS = ["Award ID", "Recipient Name", "Description", "Award Amount", "Start Date", "End Date", "Place of Performance State Code",
          "Place of Performance Zip5", "CFDA Number", "generated_internal_id"]
awards, page = {}, 1
filters = {"program_numbers": ["16.726"], "award_type_codes": ["02", "03", "04", "05"],
           "time_period": [{"start_date": "2014-10-01", "end_date": "2024-09-30"}]}
while True:
    d = post("/search/spending_by_award/", {"filters": filters, "fields": FIELDS, "limit": 100, "page": page,
                                             "sort": "Award Amount", "order": "desc"})
    for r in d["results"]:
        awards[r["generated_internal_id"]] = {k: redact(r.get(k)) for k in FIELDS}
    if not d["page_metadata"].get("hasNext"):
        break
    page += 1; time.sleep(0.3)
ma = RAW / "mentoring_awards.jsonl"
with open(ma, "w") as f:
    for a in sorted(awards.values(), key=lambda x: x["generated_internal_id"]):
        f.write(json.dumps(a) + "\n")
print(f"county rows {len(rows)}; mentoring awards {len(awards)}")

lock_path = ROOT / "data" / "sources.lock.csv"
lock = list(csv.DictReader(open(lock_path))) if lock_path.exists() else []
for p, url in [(ct, API + "/search/spending_by_geography/ (16.726, 84.334, 84.047, 84.044; FY2015-2024; place of performance)"),
               (ma, API + "/search/spending_by_award/ (16.726 grants with activity FY2015-2024)")]:
    rel = str(p.relative_to(ROOT / "data" / "raw"))
    lock = [r for r in lock if r["file"] != rel]
    lock.append({"file": rel, "url": url, "downloaded_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
                 "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
with open(lock_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["file", "url", "downloaded_utc", "bytes", "sha256"], extrasaction="ignore")
    w.writeheader(); w.writerows(lock)
