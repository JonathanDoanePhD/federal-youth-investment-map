# API sources (fetched by scripts, no login)

These sources have no bulk file, so scripts query public, keyless APIs. Each fetch writes a
record of the query, the date, the row count and the sha256 of the saved file to
`data/sources.lock.csv`, using the same format as `scripts/fetch_data.py`.

| Script | API | What | Terms |
|---|---|---|---|
| `scripts/01_fetch_nsf.py` | NSF Award Search API, `https://api.nsf.gov/services/v1/awards.json` | Awards dated 2014-2024 in six youth-facing STEM education programs: ITEST, AISL, DRK-12, CSforAll, INCLUDES, STEM+C | U.S. government work (public domain). **Personal fields such as PI and program officer names, emails and phones are dropped before saving.** |
| `scripts/02_fetch_usaspending.py` | USAspending API, `https://api.usaspending.gov/api/v2/` | Award-level grants and county totals for Assistance Listings 16.726 (OJJDP Juvenile Mentoring), 84.334 (GEAR UP), 84.047 (Upward Bound) and 84.044 (Talent Search), FY2015-2024 | Public domain (U.S. Treasury DATA Act data) |

The NSF bulk-download page (`/awardsearch/download`) now redirects to the search page, so the
API is the only scripted route (checked 2026-11-19).
