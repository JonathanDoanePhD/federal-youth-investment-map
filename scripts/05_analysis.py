"""Federal youth STEM and mentoring investment: what it funds and where it goes.

python3 -I scripts/05_analysis.py
Inputs: data/raw (NSF awards, USAspending), data/coded (agent tags; partial tags are fine),
Project 01's county table (need index, children, priority flag).
Outputs (output/):
  nsf_awards_tagged.csv      one row per NSF award: program, year, dollars, county, tags
  model_mix.csv              awards and dollars by tag value (all years) and by year for key tags
  terminations.csv           share of 2021-2024 awards (active in 2025) administratively terminated, by tag value
  need_quintile_shares.csv   share of children vs share of dollars by county need quintile, per funding stream
  priority_counties.csv      dollars reaching Project 01's 124 priority counties, per funding stream
  ojjdp_mentoring.csv        mentoring grants by organization scope, purpose and target
  investment_summary.json    headline numbers
  fig_need_shares.png, fig_model_trends.png, fig_terminations.png, fig_map.png
Location is the place of performance recorded by the agency (usually the grantee's address),
which is not always where youth are served; analyses restricted to locally delivered awards
use the agents' service_geography / org_scope tags.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapefile
from matplotlib.collections import PolyCollection

ROOT = Path(__file__).resolve().parents[1]
RAW, C, OUT = ROOT / "data" / "raw", ROOT / "data" / "coded", ROOT / "output"
OUT.mkdir(exist_ok=True)
P01 = ROOT / "data" / "external" / "county_table_project01.csv"
summary = {}

# ---------- county reference (Project 01) ----------
ct = pd.read_csv(P01, dtype={"fips": str})
ct["fips"] = ct.fips.str.zfill(5)
ct = ct[["fips", "state", "county_name", "children_0_17_acs2022", "need_index", "priority_flag", "mobility_p25_income_rank",
         "economic_connectedness"]].copy()
ct["need_quintile"] = pd.qcut(ct.need_index.rank(method="first"), 5, labels=["Q1 lowest need", "Q2", "Q3", "Q4", "Q5 highest need"])

# ZIP (ZCTA) -> county with the largest land-area share
z = pd.read_csv(RAW / "census" / "tab20_zcta520_county20_natl.txt", sep="|", dtype=str, encoding="utf-8-sig")
z = z[z.GEOID_ZCTA5_20.notna() & (z.GEOID_ZCTA5_20 != "")]
z["land"] = pd.to_numeric(z.AREALAND_PART, errors="coerce")
zip2county = z.sort_values("land", ascending=False).drop_duplicates("GEOID_ZCTA5_20").set_index("GEOID_ZCTA5_20").GEOID_COUNTY_20
_zs = sorted(zip2county.index)


def zip_to_county(zip5):
    """ZCTA lookup; for non-residential ZIPs (universities, PO boxes) use the numerically nearest ZCTA with the same 3-digit prefix."""
    if not isinstance(zip5, str) or len(zip5) < 5 or not zip5.isdigit():
        return None
    if zip5 in zip2county.index:
        return zip2county[zip5]
    same = [x for x in _zs if x[:3] == zip5[:3]]
    return zip2county[min(same, key=lambda x: abs(int(x) - int(zip5)))] if same else None


# ---------- NSF awards + tags ----------
nsf = pd.DataFrame([json.loads(l) for l in open(RAW / "nsf" / "awards.jsonl")])
nsf["year"] = nsf.date.str[-4:].astype(int)
nsf["dollars"] = pd.to_numeric(nsf.fundsObligatedAmt, errors="coerce").fillna(0)
nsf["terminated"] = nsf.awdSpAttnDesc.fillna("").str.contains("Terminated")
nsf["zip5"] = nsf.perfZipCode.fillna("").str[:5]
nsf["county_fips"] = nsf.zip5.map(zip_to_county).fillna(nsf.awardeeZipCode.fillna("").str[:5].map(zip_to_county))  # fall back to grantee ZIP
nsf["programs"] = nsf.query_programs.apply(lambda x: ";".join(x))
# collaborative awards share one project: group by title without the "Collaborative Research:" prefix
nsf["project_key"] = (nsf.title.str.replace(r"^\s*collaborative research\s*:\s*", "", case=False, regex=True)
                      .str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip())
tags = {str(e["id"]): e for f in sorted((C / "nsf" / "main").glob("batch_*.json")) for e in json.loads(f.read_text())}
TAGF = ["serves_youth", "audience", "grade_band", "models", "mentoring", "bridging", "ai_cs", "targets", "setting", "youth_reach",
        "evaluation", "service_geography"]
for f in TAGF:
    nsf[f] = nsf.id.map(lambda i: tags.get(str(i), {}).get(f))
nsf["tagged"] = nsf.id.astype(str).isin(tags)
keep = ["id", "project_key", "title", "programs", "year", "dollars", "terminated", "perfStateCode", "county_fips", "awardeeName", "tagged"] + TAGF
nt = nsf[keep].copy()
for f in ["audience", "models", "targets"]:
    nt[f] = nt[f].apply(lambda x: ";".join(x) if isinstance(x, list) else None)
nt.to_csv(OUT / "nsf_awards_tagged.csv", index=False)
summary["nsf"] = {"awards": int(len(nsf)), "projects": int(nsf.project_key.nunique()), "dollars_obligated": float(nsf.dollars.sum()), "tagged": int(nsf.tagged.sum()),
                  "terminated_awards": int(nsf.terminated.sum()), "terminated_share": float(nsf.terminated.mean()),
                  "mapped_to_county": float(nsf.county_fips.notna().mean())}

tg = nsf[nsf.tagged].copy()
if len(tg):
    rows = []
    for f in ["serves_youth", "grade_band", "mentoring", "bridging", "ai_cs", "setting", "evaluation", "service_geography"]:
        base = tg[tg.serves_youth != "none"] if f == "evaluation" else tg  # evaluation: youth-serving awards only (protocol 1.0a)
        for v, g in base.groupby(f):
            rows.append({"tag": f, "value": v, "awards": len(g), "share_awards": len(g) / len(base), "dollars": g.dollars.sum(),
                         "share_dollars": g.dollars.sum() / base.dollars.sum()})
    for f in ["audience", "models", "targets"]:
        ex = tg.explode(f)
        for v, g in ex.groupby(f):
            rows.append({"tag": f, "value": v, "awards": g.id.nunique(), "share_awards": g.id.nunique() / len(tg),
                         "dollars": g.dollars.sum(), "share_dollars": g.dollars.sum() / tg.dollars.sum()})
    mix = pd.DataFrame(rows)
    # trend: share of awards per year for key tag values
    trend = []
    for y, g in tg.groupby("year"):
        trend.append({"year": y, "awards": len(g), "ai": (g.ai_cs == "ai").mean(), "computing_or_ai": (g.ai_cs != "none").mean(),
                      "mentoring_any": (g.mentoring != "none").mean(), "mentoring_central": (g.mentoring == "central").mean(),
                      "bridging": (g.bridging == "yes").mean(), "direct_youth": (g.serves_youth == "direct").mean(),
                      "rigorous_eval": g[g.serves_youth != "none"].evaluation.isin(["rct", "quasi_experimental"]).mean()})
    trend = pd.DataFrame(trend)
    mix.to_csv(OUT / "model_mix.csv", index=False, float_format="%.4f")
    trend.to_csv(OUT / "model_trends_by_year.csv", index=False, float_format="%.4f")

    # Terminations (2025) hit awards still active then, i.e. awards dated 2021-2024; compare within that cohort.
    act = tg[tg.year >= 2021]
    term = [{"tag": "all", "value": "awards dated 2021-2024", "awards": len(act), "terminated": int(act.terminated.sum()),
             "share_terminated": act.terminated.mean(), "dollars_terminated_share": act[act.terminated].dollars.sum() / act.dollars.sum()}]
    for f in ["serves_youth", "mentoring", "bridging", "ai_cs", "evaluation", "service_geography"]:
        for v, g in act.groupby(f):
            term.append({"tag": f, "value": v, "awards": len(g), "terminated": int(g.terminated.sum()), "share_terminated": g.terminated.mean(),
                         "dollars_terminated_share": g[g.terminated].dollars.sum() / g.dollars.sum() if g.dollars.sum() else np.nan})
    for f in ["targets", "models"]:
        ex = act.explode(f)
        for v, g in ex.groupby(f):
            term.append({"tag": f, "value": v, "awards": g.id.nunique(), "terminated": int(g[g.terminated].id.nunique()),
                         "share_terminated": g.drop_duplicates("id").terminated.mean(), "dollars_terminated_share": np.nan})
    pd.DataFrame(term).to_csv(OUT / "terminations.csv", index=False, float_format="%.4f")
    summary["nsf_tags"] = {
        "direct_youth_share": float((tg.serves_youth == "direct").mean()),
        "mentoring_any_share": float((tg.mentoring != "none").mean()), "mentoring_central_share": float((tg.mentoring == "central").mean()),
        "bridging_share": float((tg.bridging == "yes").mean()), "ai_share": float((tg.ai_cs == "ai").mean()),
        "ai_share_2014_2019": float((tg[tg.year <= 2019].ai_cs == "ai").mean()) if (tg.year <= 2019).any() else None,
        "ai_share_2022_2024": float((tg[tg.year >= 2022].ai_cs == "ai").mean()) if (tg.year >= 2022).any() else None,
        "rigorous_eval_share_youth_serving": float(tg[tg.serves_youth != "none"].evaluation.isin(["rct", "quasi_experimental"]).mean()),
    }

# ---------- USAspending ----------
cty = pd.read_csv(RAW / "usaspending" / "county_totals.csv", dtype={"county_fips": str, "cfda": str})
cty = cty[cty.county_fips.notna()]
cty["county_fips"] = cty.county_fips.str.zfill(5)
oj = pd.DataFrame([json.loads(l) for l in open(RAW / "usaspending" / "mentoring_awards.jsonl")])
ojt = {str(e["id"]): e for f in sorted((C / "ojjdp").glob("batch_*.json")) for e in json.loads(f.read_text())}
for f in ["org_scope", "targets", "format", "purpose"]:
    oj[f] = oj.generated_internal_id.map(lambda i: ojt.get(i, {}).get(f))
oj["year"] = oj["Start Date"].str[:4]
oj["zip5"] = oj["Place of Performance Zip5"].fillna("").str[:5]
oj["county_fips"] = oj.zip5.map(zip_to_county)
if oj.org_scope.notna().any():
    r = []
    for f in ["org_scope", "format", "purpose"]:
        for v, g in oj[oj[f].notna()].groupby(f):
            r.append({"tag": f, "value": v, "grants": len(g), "dollars": g["Award Amount"].sum(),
                      "share_dollars": g["Award Amount"].sum() / oj[oj[f].notna()]["Award Amount"].sum()})
    ex = oj[oj.targets.notna()].explode("targets")
    for v, g in ex.groupby("targets"):
        r.append({"tag": "targets", "value": v, "grants": g.generated_internal_id.nunique(), "dollars": g["Award Amount"].sum(),
                  "share_dollars": g["Award Amount"].sum() / oj[oj.targets.notna()]["Award Amount"].sum()})
    pd.DataFrame(r).to_csv(OUT / "ojjdp_mentoring.csv", index=False, float_format="%.4f")
    summary["ojjdp"] = {"grants": int(len(oj)), "dollars": float(oj["Award Amount"].sum()),
                        "national_multisite_dollar_share": float(oj[oj.org_scope == "national_multisite"]["Award Amount"].sum() / oj[oj.org_scope.notna()]["Award Amount"].sum())}

# ---------- where the money goes: need quintiles and priority counties ----------
streams = {}
streams["NSF youth STEM (all awards)"] = nsf.groupby("county_fips").dollars.sum()
if len(tg):
    d = tg[tg.serves_youth == "direct"]
    streams["NSF: youth served directly"] = d.groupby("county_fips").dollars.sum()
    loc = tg[(tg.serves_youth == "direct") & tg.service_geography.isin(["local", "state_regional"])]
    streams["NSF: direct youth, local/state delivery"] = loc.groupby("county_fips").dollars.sum()
    mb = tg[(tg.mentoring != "none") | (tg.bridging == "yes")]
    streams["NSF: mentoring or bridging"] = mb.groupby("county_fips").dollars.sum()
for name, cf in [("OJJDP mentoring (all)", ["16.726"]), ("College access: GEAR UP, Upward Bound, Talent Search", ["84.334", "84.047", "84.044"])]:
    streams[name] = cty[cty.cfda.isin(cf)].groupby("county_fips").amount.sum()
if oj.org_scope.notna().any():
    streams["OJJDP mentoring: local/state grantees"] = oj[oj.org_scope.isin(["local", "state_regional", "tribal"])].groupby("county_fips")["Award Amount"].sum()

qrows, prows = [], []
kids_tot = ct.children_0_17_acs2022.sum()
for name, s in streams.items():
    m = ct.merge(s.rename("dollars"), left_on="fips", right_index=True, how="left").fillna({"dollars": 0})
    tot = m.dollars.sum()
    for q, g in m.groupby("need_quintile", observed=True):
        qrows.append({"stream": name, "need_quintile": q, "share_children": g.children_0_17_acs2022.sum() / kids_tot,
                      "share_dollars": g.dollars.sum() / tot if tot else np.nan,
                      "dollars_per_child": g.dollars.sum() / g.children_0_17_acs2022.sum(),
                      "share_counties_with_none": (g.dollars == 0).mean()})
    p = m[m.priority_flag == True]
    prows.append({"stream": name, "total_dollars": tot, "priority_counties": len(p), "priority_counties_with_any": int((p.dollars > 0).sum()),
                  "share_children_in_priority": p.children_0_17_acs2022.sum() / kids_tot, "share_dollars_in_priority": p.dollars.sum() / tot if tot else np.nan,
                  "dollars_per_child_priority": p.dollars.sum() / p.children_0_17_acs2022.sum(),
                  "dollars_per_child_national": tot / kids_tot})
qs = pd.DataFrame(qrows); qs.to_csv(OUT / "need_quintile_shares.csv", index=False, float_format="%.4f")
pr = pd.DataFrame(prows); pr.to_csv(OUT / "priority_counties.csv", index=False, float_format="%.4f")
summary["priority_counties"] = pr.round(4).to_dict(orient="records")

# ---------- figures ----------
fig, ax = plt.subplots(figsize=(10.5, 0.75 * len(streams) + 2.2), dpi=100)
qlab = ["Q1 lowest need", "Q2", "Q3", "Q4", "Q5 highest need"]
names = list(streams)
for k, name in enumerate(names):
    g = qs[qs.stream == name].set_index("need_quintile").reindex(qlab)
    ratio = g.share_dollars / g.share_children
    for j, q in enumerate(qlab):
        if not np.isfinite(ratio[q]):
            continue
        ax.scatter(j, k, s=60 + 900 * min(ratio[q], 3) / 3, color="#2a78d6" if ratio[q] >= 1 else "#eb6834", alpha=0.8)
        ax.text(j, k + 0.33, f"{ratio[q]:.2f}", ha="center", fontsize=8.5, color="#0b0b0b")
ax.set_xticks(range(5), qlab); ax.set_yticks(range(len(names)), names); ax.set_ylim(-0.6, len(names) - 0.3); ax.invert_yaxis()
ax.set_title("Dollars per child relative to the national average, by county need quintile (1.00 = fair share)", loc="left", fontsize=11)
fig.text(0.01, 0.01, "Need index from Project 01 (child poverty, vulnerability, low mobility). Location = recorded place of performance, often the "
         "grantee's address. Blue >= 1, orange < 1. Verify before external use.", fontsize=7.5, color="#52514e")
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(OUT / "fig_need_shares.png", dpi=150); plt.close(fig)

if len(tg):
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=100)
    for col, lab, colr in [("computing_or_ai", "Computing or AI focus", "#2a78d6"), ("ai", "AI focus", "#eb6834"),
                           ("mentoring_any", "Any mentoring", "#1a8a5a"), ("bridging", "Bridging to professionals/networks", "#7a4fc0"),
                           ("rigorous_eval", "Randomized or comparison-group evaluation", "#52514e")]:
        ax.plot(trend.year, trend[col] * 100, marker="o", ms=4, lw=2, color=colr, label=lab)
    ax.set_ylabel("Share of tagged awards (%)"); ax.set_ylim(0, None); ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, fontsize=8.5); ax.set_title("What NSF youth STEM education awards fund, 2014-2024", loc="left", fontsize=12)
    fig.text(0.01, 0.01, "Six NSF programs (ITEST, AISL, DRK-12, CSforAll, INCLUDES, STEM+C); tags by AI agents from abstracts. Verify before external use.",
             fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(OUT / "fig_model_trends.png", dpi=150); plt.close(fig)

if len(tg):
    tt = pd.read_csv(OUT / "terminations.csv")
    sel = pd.concat([tt[tt.tag == "all"],
                     tt[(tt.tag == "targets") & (tt.awards >= 40)],
                     tt[(tt.tag == "mentoring") & (tt.value == "central")],
                     tt[(tt.tag == "bridging") & (tt.value == "yes")],
                     tt[(tt.tag == "ai_cs") & (tt.value == "ai")]])
    lab = {"awards dated 2021-2024": "All awards dated 2021-2024", "general": "No specific group named", "black": "Black youth",
           "hispanic_latino": "Hispanic/Latino youth", "native_indigenous": "Native/Indigenous youth", "girls_women": "Girls and women",
           "low_income": "Low-income youth", "underrepresented_general": "'Underrepresented' (unspecified)", "rural": "Rural youth",
           "urban": "Urban youth", "disability": "Youth with disabilities", "english_learners": "English learners",
           "central": "Mentoring central to design", "yes": "Bridging to professionals/networks", "ai": "AI focus"}
    sel = sel.assign(label=sel.value.map(lab).fillna(sel.value)).sort_values("share_terminated")
    fig, ax = plt.subplots(figsize=(9.5, 0.42 * len(sel) + 1.8), dpi=100)
    colors = ["#52514e" if v == "awards dated 2021-2024" else "#eb6834" if s > 0.3 else "#2a78d6" for v, s in zip(sel.value, sel.share_terminated)]
    ax.barh(sel.label, sel.share_terminated * 100, color=colors)
    for y, (s, n) in enumerate(zip(sel.share_terminated, sel.awards)):
        ax.text(s * 100 + 0.8, y, f"{s:.0%} of {n}", va="center", fontsize=8.5)
    ax.set_xlabel("Share of awards administratively terminated (%)"); ax.set_xlim(0, max(sel.share_terminated) * 118)
    ax.set_title("NSF youth STEM awards dated 2021-2024: share terminated, by what the abstract names", loc="left", fontsize=11)
    fig.text(0.01, 0.01, "Groups overlap (an award can name several). Tags by AI agents from abstracts; termination flag from NSF Award API (checked 2026-11-19). "
             "Associations only. Verify before external use.", fontsize=7.3, color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(OUT / "fig_terminations.png", dpi=150); plt.close(fig)

# Map: combined youth mentoring + college access + NSF direct-youth dollars per child, priority counties outlined
def albers(lon, lat, lat1=29.5, lat2=45.5, lat0=37.5, lon0=-96.0):
    p = np.radians; n = (np.sin(p(lat1)) + np.sin(p(lat2))) / 2; Cc = np.cos(p(lat1)) ** 2 + 2 * n * np.sin(p(lat1))
    rho = lambda la: np.sqrt(Cc - 2 * n * np.sin(p(la))) / n; th = n * p(np.asarray(lon) - lon0); r = rho(np.asarray(lat))
    return r * np.sin(th), rho(lat0) - r * np.cos(th)

comb = sum(s.reindex(ct.fips).fillna(0).values for k, s in streams.items()
           if k in ("OJJDP mentoring (all)", "College access: GEAR UP, Upward Bound, Talent Search", "NSF youth STEM (all awards)"))
per_child = pd.Series(comb / ct.children_0_17_acs2022.clip(lower=1).values, index=ct.fips.values)
bins = [-1, 0, 50, 200, 1000, np.inf]; cols = ["#e4e3df", "#cfe0f3", "#8db8e6", "#2a78d6", "#0f4c99"]
labels = ["None", "<$50", "$50-200", "$200-1,000", ">$1,000"]
pri = set(ct[ct.priority_flag == True].fips)
sf = shapefile.Reader(str(RAW / "shapes" / "cb_2022_us_county_20m.shp"))
polys = {k: [] for k in range(5)}; pri_polys = []
for rec, shp in zip(sf.records(), sf.shapes()):
    if rec["STATEFP"] in ("02", "15", "72"):
        continue
    v = per_child.get(rec["GEOID"], 0); k = int(np.digitize(v, bins[1:-1], right=True)) if v > 0 else 0
    pts = np.array(shp.points)
    for a, b in zip(shp.parts, list(shp.parts[1:]) + [len(pts)]):
        x, y = albers(pts[a:b, 0], pts[a:b, 1]); xy = np.column_stack([x, y])
        polys[k].append(xy)
        if rec["GEOID"] in pri:
            pri_polys.append(xy)
fig, ax = plt.subplots(figsize=(13, 8.4), dpi=100)
for k in range(5):
    ax.add_collection(PolyCollection(polys[k], facecolors=cols[k], edgecolors="#fcfcfb", linewidths=0.2))
ax.add_collection(PolyCollection(pri_polys, facecolors="none", edgecolors="#eb6834", linewidths=1.1))
ax.autoscale_view(); ax.set_aspect("equal"); ax.axis("off")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=c, label=l) for c, l in zip(cols, labels)] + [Patch(fc="none", ec="#eb6834", label="Project 01 priority county")],
          title="Federal youth STEM, mentoring and college-access $ per child\n(NSF 2014-24, OJJDP + TRIO/GEAR UP FY2015-24)",
          loc="lower left", frameon=False, fontsize=9, title_fontsize=9)
fig.text(0.01, 0.01, "Place of performance is often the grantee's headquarters (e.g. national youth organizations), so money is shown where it is "
         "recorded, not necessarily where youth are served. Verify before external use.", fontsize=7.5, color="#52514e")
fig.tight_layout(); fig.savefig(OUT / "fig_map.png", dpi=150); plt.close(fig)

(OUT / "investment_summary.json").write_text(json.dumps(summary, indent=2, default=str))
print(json.dumps(summary, indent=1, default=str)[:4000])
