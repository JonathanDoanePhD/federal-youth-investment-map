# 09 - Federal Youth Program Investment Map

**Question:** Where does federal money for youth STEM and youth mentoring go, which program
models does it fund, and does it reach the places with the greatest need (Project 01's need
index and priority counties)?

**Status:** first pass complete (2026-11-20). All 2,974 NSF awards and 390 OJJDP grants are
tagged and validated, and reliability and analysis outputs are built. Next: a person
spot-checks a sample of tags, and the termination findings are checked against NSF's own
lists (see Next steps).

> **Exploratory, AI-assisted research.** Award tags come from Claude agents reading abstracts
> under [docs/protocol.md](docs/protocol.md), with validation and a second, independent
> reference-model pass on 320 awards. Dollar figures come from federal APIs. All figures need
> verification against the original sources before they go to funders or the public.

## Key findings

1. **AI is the fastest-growing focus; mentoring stays rare.** In six NSF youth STEM programs,
   awards with an explicit AI focus rose from **2% (2014) to 21% (2024)**. Awards with any
   computing or AI focus rose from 20% to 47%. Over the same years, only **14% of awards
   include mentoring and 3% make it central**, with no upward trend. 13% deliberately connect
   youth to professionals or networks beyond their usual circles (`output/model_trends_by_year.csv`,
   `fig_model_trends.png`).
2. **Few awards plan rigorous evaluations, and fewer over time.** Among awards that involve
   youth, 14% plan a randomized or comparison-group evaluation. That share fell from 17% in
   2014 to 8% in 2024. This fits Project 08's finding that strong designs are scarce and are
   the ones worth trusting.
3. **NSF youth STEM money reaches high-need places least.** Counties in the highest-need fifth
   (Project 01's index) receive **0.46 times their per-child share** of these NSF dollars. The
   lowest-need fifth gets 1.63 times its share. The gap remains for awards delivered locally
   with youth served directly (0.58).
   - By contrast, the college-access programs (GEAR UP, Upward Bound, Talent Search), which
     target by design, give the highest-need fifth **1.40 times** its share.
   - Grants to local and state mentoring organizations from the Justice Department's youth
     mentoring program (OJJDP) come close to parity (0.91).
4. **Project 01's 124 priority counties are nearly invisible to these streams.**
   - NSF youth STEM awards are recorded in 2 of them.
   - Local and state OJJDP mentoring grants are recorded in none of them.
   - College-access grants are recorded in 8, at about the national level per child ($128 vs.
     $122).
   - These counties hold about 0.5% of U.S. children, so programs serving them from a nearby
     hub would not show here.
5. **Federal mentoring money flows mostly through national intermediaries.** 79% of $1.04B in
   OJJDP mentoring grants (2015-2024 activity) went to national organizations that fund local
   sites. Most grants are general youth development (70% of dollars). The main targeted groups
   are youth at risk (22%), justice-involved youth (13%), opioid-affected youth (10%) and
   Native youth (8%). Grant descriptions rarely say whether mentoring is one-to-one or in
   groups (79% of dollars unclear).
6. **The 2025 terminations fell hardest on awards naming specific groups.**
   - Among awards dated 2021-2024 (those still active in 2025), **20% were administratively
     terminated** (`fig_terminations.png`).
   - The rate was 56% for abstracts naming Black youth, 54% for Hispanic/Latino youth, 46% for
     girls and women, 45% for Native/Indigenous youth and 33% where mentoring is central.
   - It was **2.5% for abstracts naming no specific group** and 6% for AI-focused awards.
   - Groups overlap, and the tags come from abstracts, so these are associations, not a
     statement of NSF's criteria.

## Reliability

A reference model tagged 320 awards (8 batches) independently of the main Sonnet pass
(`output/tagging_reliability.csv`). Kappa (agreement beyond chance; 1 is perfect) on each field:

| Field | Kappa |
|---|---|
| AI/CS focus | 0.99 |
| Grade band | 0.92 |
| Serves youth (direct, indirect, none) | 0.91 |
| Service geography | 0.87 |
| Mentoring role | 0.85 |
| Evaluation design (youth-serving awards) | 0.80 |
| Rigorous evaluation, yes or no | 0.98 |
| Setting | 0.79 |
| Bridging | 0.71 |

List fields overlap well: mean Jaccard 0.82 for audience, 0.83 for models and 0.89 for target
groups. Bridging is the least reliable tag, as it was in Project 08.

## Sources

| Source | What | How |
|---|---|---|
| NSF Award Search API | 2,974 awards (2,395 projects; $3.39B obligated) dated 2014-2024 in six youth-facing STEM education programs: ITEST, AISL (informal STEM learning), DRK-12, CSforAll, INCLUDES, STEM+C | `scripts/01_fetch_nsf.py`; personal fields dropped at fetch |
| USAspending API | 390 OJJDP Juvenile Mentoring grants (16.726) with activity in FY2015-2024, and county totals for 16.726, GEAR UP (84.334), Upward Bound (84.047) and Talent Search (84.044) | `scripts/02_fetch_usaspending.py` |
| Census | 2020 ZIP (ZCTA)-to-county file; 2022 county boundaries | `scripts/fetch_data.py` |
| Project 01 | County need index, children 0-17, the 124 priority counties | `data/external/county_table_project01.csv` |

The NSF bulk-download page now redirects to the search page, so the keyless API is used (see
`data/api_sources.md`).

## How it works

| Step | What happens |
|---|---|
| Fetch | API pulls; each saved file's sha256 recorded in `data/sources.lock.csv` |
| Tag (agents) | Every NSF abstract is read in full and tagged for whom it serves, program models, mentoring role, bridging, AI/CS focus, targeted groups, setting, evaluation design and service geography (75 batches). Every OJJDP grant is tagged for organization scope, targets, format and purpose (8 batches) |
| Check | Validator (schema, IDs, allowed values, row-alignment check); a second pass by the reference model on 8 NSF batches gives agreement and kappa |
| Map | ZIP of performance → county (largest land share; nearest residential ZIP for university/PO-box ZIPs) → Project 01 need quintiles and priority counties |

## Rebuild

From this folder:

```bash
python3 -I scripts/fetch_data.py .
python3 -I scripts/01_fetch_nsf.py
python3 -I scripts/02_fetch_usaspending.py
python3 -I scripts/03_make_batches.py
# tagging: see RESUME.md (agent workflow); committed tags in data/coded/ are the record
python3 -I scripts/04_reliability.py
python3 -I scripts/05_analysis.py
```

## Outputs

| File | What |
|---|---|
| `output/nsf_awards_tagged.csv` | One row per NSF award: project key, program, year, dollars, county, termination flag, tags |
| `output/model_mix.csv`, `model_trends_by_year.csv` | Awards and dollars by tag; yearly shares (AI, computing, mentoring, bridging, rigorous evaluation) |
| `output/terminations.csv` | Share of awards administratively terminated, by tag |
| `output/need_quintile_shares.csv` | Share of children vs. share of dollars by county need quintile, per funding stream |
| `output/priority_counties.csv` | Dollars reaching Project 01's priority counties, per stream |
| `output/ojjdp_mentoring.csv` | Mentoring grants by organization scope, purpose, format and target group |
| `output/tagging_reliability.csv` | Main vs. reference agreement per field |
| `output/investment_summary.json` | Headline numbers |
| `output/fig_need_shares.png`, `fig_model_trends.png`, `fig_terminations.png`, `fig_map.png` | Figures |
| `data/coded/nsf/main/`, `nsf/reference/`, `ojjdp/` | All agent tags (no abstract text; short paraphrased notes) |

## Columns in `nsf_awards_tagged.csv`

`id`, `project_key` (title without "Collaborative Research:", which groups split awards),
`title`, `programs`, `year` (award date), `dollars` (obligated), `terminated` (administratively
terminated flag), `perfStateCode`, `county_fips`, `awardeeName` (organization), `tagged`, plus
the protocol tags: `serves_youth`, `audience`, `grade_band`, `models`, `mentoring`,
`bridging`, `ai_cs`, `targets`, `setting`, `youth_reach`, `evaluation`, `service_geography`.
List fields are separated by `;`. Definitions are in [docs/protocol.md](docs/protocol.md).

## Caveats

- **Location is where the money is recorded,** usually the grantee's address. National
  organizations and universities can serve youth far away. Analyses restricted to locally
  delivered awards use the agents' `service_geography` / `org_scope` tags.
- **Six NSF programs, not all federal STEM spending.** Other agencies (NASA, DoD STEM, ED's
  21st Century Community Learning Centers, AmeriCorps) are not included.
- **Obligated, not spent.** NSF `fundsObligatedAmt` is the amount obligated to date;
  terminated awards may have spent less.
- **Tags come from abstracts,** which describe plans, not delivery.
- Project 01's priority counties hold about 0.5% of U.S. children, so dollar shares there are
  small by construction; dollars per child are the fairer comparison.
- **Terminations:** the flag is what the NSF Award API showed on 2026-11-19. Some
  terminations were later contested or reversed, and the API may not reflect every change.
  Group names come from abstracts, and groups overlap.
- **Reliability is model-to-model.** Both passes are AI models; agreement is not accuracy.

## Next steps

- **Human spot-check:** a person reviews 50 random awards (stratified by tag) against their
  abstracts. Record the results here.
- **Verify the termination figures** against NSF's published list of terminated awards
  before any external use. Use the figures only with human review, given their policy
  sensitivity.
- **Extend coverage:** add other federal youth STEM streams (NASA, DoD STEM, ED's 21st Century
  Community Learning Centers) through USAspending.
- **Service areas:** for national intermediaries, map their local affiliates (for example,
  from IRS exempt-organization files) to see where mentoring money is actually spent. This
  links naturally to project #2 (Nonprofit Program DNA).

## License, citation and data terms

- **Code:** MIT (see `LICENSE`). **Outputs:** CC BY 4.0, subject to the source terms below.
- **Cite this project as:** JonathanDoanePhD (2026). *Federal Youth Program Investment Map*. https://github.com/JonathanDoanePhD/federal-youth-investment-map
- **Data sources and terms** (from `data/sources.csv`; recorded versions and checksums in `data/sources.lock.csv`):

| Source | Terms |
|---|---|
| U.S. Census Bureau 2020 ZCTA-to-county relationship file | Public domain (U.S. government work) |
| Census cartographic county boundaries 2022 | Public domain (U.S. government work) |

Built with AI assistance (Claude). Exploratory research: every statistic needs checking against its original source
before it appears in funder reports, grant applications or public material.

## Status and limitations

Published 2026-11-26 as exploratory research. The analysis is complete and reproducible, but these checks have **not yet been done**, so treat figures as provisional:

- Statistics in this README and in `output/` have not been independently checked against their original sources.
- A person spot-checks 50 award tags.
- Verify the 2025 termination figures against NSF's published list; human review before any external use (policy sensitive).
