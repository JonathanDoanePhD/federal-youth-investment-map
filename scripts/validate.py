"""Validate an agent's tagging file against docs/protocol.md. Exit code 0 = valid.

python3 -I scripts/validate.py nsf   data/coded/nsf/main/batch_0001.json
python3 -I scripts/validate.py nsf   data/coded/nsf/reference/batch_0003.json
python3 -I scripts/validate.py ojjdp data/coded/ojjdp/batch_0001.json
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NSF_ENUM = {
    "serves_youth": {"direct", "indirect", "none"},
    "grade_band": {"prek", "elementary", "middle", "high", "k12_mixed", "mixed_ages", "not_applicable"},
    "mentoring": {"central", "component", "none"},
    "bridging": {"yes", "no", "unclear"},
    "ai_cs": {"ai", "computing", "none"},
    "setting": {"school_day", "after_school", "summer", "museum_science_center", "library", "online", "home_family",
                "college_campus", "workplace", "community", "mixed", "unclear"},
    "evaluation": {"rct", "quasi_experimental", "pre_post", "design_qualitative", "unspecified", "none_stated"},
    "service_geography": {"local", "state_regional", "multi_state", "national", "unclear"},
}
NSF_LISTS = {
    "audience": {"k12_students", "out_of_school_youth", "families", "teachers_educators", "undergraduates", "general_public", "researchers"},
    "models": {"mentoring", "research_apprenticeship", "out_of_school_program", "summer_program", "school_curriculum", "teacher_pd",
               "exhibit_media", "career_exposure", "online_tool_game", "research_only", "network_coalition", "other"},
    "targets": {"low_income", "black", "hispanic_latino", "native_indigenous", "girls_women", "rural", "urban", "disability",
                "english_learners", "first_generation", "underrepresented_general", "general"},
}
OJ_ENUM = {
    "org_scope": {"national_multisite", "state_regional", "local", "tribal", "unclear"},
    "format": {"one_to_one", "group", "peer", "mixed", "unclear"},
    "purpose": {"youth_development", "delinquency_prevention", "reentry", "career_workforce", "academic", "research_evaluation",
                "training_technical_assistance", "unclear"},
}
OJ_LISTS = {"targets": {"opioid_substance_affected", "justice_involved", "at_risk_general", "children_of_incarcerated", "foster_care",
                        "tribal_native", "disability", "girls", "boys_young_men_of_color", "military_families", "general", "other"}}
STOPW = set("the a an of and or for in on to with by from at as is are was were be this that these those not no project projects "
            "will youth students student stem science learning program programs research education award nsf".split())


def words(s):
    return len(str(s or "").split())


def alignment(kind, path, out):
    w = lambda t: {x for x in re.findall(r"[a-z]{4,}", str(t).lower()) if x not in STOPW}
    inp = [json.loads(l) for l in open(ROOT / "data" / "interim" / "batches" / kind / f"{Path(path).stem}.jsonl")]
    tx = [w(r["title"] + " " + r.get("abstract", "") + " " + (r.get("organization") or "")) for r in inp]
    wins = n = 0
    for i, r in enumerate(inp):
        rw = w(out.get(r["id"], {}).get("notes", ""))
        if len(rw) < 2:
            continue
        own = len(rw & tx[i]); nb = max(len(rw & tx[j]) for j in (i - 1, i + 1) if 0 <= j < len(inp))
        n += 1; wins += 1 if own > nb else (0.5 if own == nb and own > 0 else 0)
    return wins / n if n else 1.0


def main(kind, path):
    try:
        data = json.loads(Path(path).read_text())
    except Exception as ex:
        print(f"INVALID JSON: {ex}"); return 1
    if not isinstance(data, list):
        print("INVALID: top level must be a list"); return 1
    expected = [json.loads(l)["id"] for l in open(ROOT / "data" / "interim" / "batches" / kind / f"{Path(path).stem}.jsonl")]
    got = [str(e.get("id")) for e in data]
    errs = []
    if sorted(got) != sorted(expected):
        m, x = set(expected) - set(got), set(got) - set(expected)
        errs.append(f"id mismatch: missing {sorted(m)[:5]} ({len(m)}), extra {sorted(x)[:5]} ({len(x)}), dupes {len(got) - len(set(got))}")
    enums, lists, maxw = (NSF_ENUM, NSF_LISTS, 20) if kind == "nsf" else (OJ_ENUM, OJ_LISTS, 15)
    for i, e in enumerate(data):
        for k, allowed in enums.items():
            if e.get(k) not in allowed:
                errs.append(f"[{i}] bad {k}={e.get(k)!r}")
        for k, allowed in lists.items():
            v = e.get(k)
            if not isinstance(v, list) or any(t not in allowed for t in v):
                errs.append(f"[{i}] bad {k}={v!r}")
        if kind == "nsf":
            if e.get("models") == []:
                errs.append(f"[{i}] models must list at least one activity")
            yr = e.get("youth_reach")
            if yr is not None and (not isinstance(yr, int) or isinstance(yr, bool) or yr < 0):
                errs.append(f"[{i}] youth_reach must be a non-negative int or null")
        if words(e.get("notes")) > maxw + 5:
            errs.append(f"[{i}] notes too long")
    if not errs:
        a = alignment(kind, path, {str(e["id"]): e for e in data})
        if a < 0.75:
            errs.append(f"notes do not match their records (alignment {a:.2f} < 0.75): tags look shifted. "
                        "Rebuild the file by matching each record's id to its own text.")
    if errs:
        print("INVALID:\n" + "\n".join(errs[:40])); return 1
    print(f"VALID: {len(data)} records"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
