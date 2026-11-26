# Protocol: Federal Youth Program Investment Map

Version 1.0 (2026-11-19). Agents follow this document exactly. Changes get a new version and a
changelog note.

## Question

Where does federal money for youth STEM and youth mentoring go, which program models does it
fund, and does it reach the places with the greatest need (Project 01)?

## Part A: NSF award tagging (one record per award)

Read the title, program and **the full abstract**. Tag only what the abstract states; use
`unclear`, `none_stated`, `null` or an empty list rather than guess.

| Field | Values |
|---|---|
| `serves_youth` | `direct`: youth take part in project activities (camps, clubs, courses, apprenticeships, exhibits). `indirect`: the project works through teachers, curricula, tools or research that reach youth later. `none`: no K-12 or out-of-school youth involved (e.g., only undergraduates, adults, or researchers) |
| `audience` | list from `k12_students`, `out_of_school_youth`, `families`, `teachers_educators`, `undergraduates`, `general_public`, `researchers` |
| `grade_band` | `prek`, `elementary`, `middle`, `high`, `k12_mixed`, `mixed_ages`, `not_applicable` |
| `models` | list of activities the award funds, from `mentoring`, `research_apprenticeship` (youth do authentic research or internships), `out_of_school_program` (clubs, after-school), `summer_program`, `school_curriculum` (courses, units, materials used in school), `teacher_pd`, `exhibit_media` (museum exhibits, TV, film, radio, public events), `career_exposure` (career talks, site visits, role models, job shadowing), `online_tool_game`, `research_only` (studies learning without delivering a program), `network_coalition` (alliances, backbone organizations, convenings), `other` |
| `mentoring` | `central` (mentoring relationships are a main part of the design), `component` (mentoring is mentioned as one of several supports), `none` |
| `bridging` | `yes` if the project deliberately connects youth to people, workplaces or networks beyond their usual circles (scientists, industry professionals, employers, college researchers, career mentors); `no`; `unclear` |
| `ai_cs` | `ai` (artificial intelligence or machine learning is an explicit focus), `computing` (computer science, coding, computational thinking, cybersecurity or data science without an AI focus), `none` |
| `targets` | list from `low_income`, `black`, `hispanic_latino`, `native_indigenous`, `girls_women`, `rural`, `urban`, `disability`, `english_learners`, `first_generation`, `underrepresented_general` (named as underrepresented/marginalized without specifics), `general` (no particular group) |
| `setting` | `school_day`, `after_school`, `summer`, `museum_science_center`, `library`, `online`, `home_family`, `college_campus`, `workplace`, `community`, `mixed`, `unclear` |
| `youth_reach` | integer number of youth the abstract says the project will serve or study, or `null` |
| `evaluation` | strongest design described for youth outcomes: `rct`, `quasi_experimental`, `pre_post`, `design_qualitative` (design-based research, case studies, interviews), `unspecified` (evaluation mentioned, design not described), `none_stated` |
| `service_geography` | `local` (one city, county or school district), `state_regional` (one state or region), `multi_state`, `national` (national reach, online, broadcast), `unclear` |
| `notes` | at most 20 words, in your own words (do not copy abstract text) |

Per record: `{"id": "1612345", "serves_youth": "direct", ..., "notes": "..."}`.

## Part B: OJJDP mentoring grant tagging

Read the recipient name, award description and state. Descriptions are short; tag only what
they and the recipient name support.

| Field | Values |
|---|---|
| `org_scope` | `national_multisite` (national organization or intermediary funding many local sites, e.g. national youth-serving federations or mentoring networks), `state_regional` (state agency, state-wide network or multi-county), `local` (a single local organization or community), `tribal`, `unclear` |
| `targets` | list from `opioid_substance_affected`, `justice_involved`, `at_risk_general`, `children_of_incarcerated`, `foster_care`, `tribal_native`, `disability`, `girls`, `boys_young_men_of_color`, `military_families`, `general`, `other` |
| `format` | `one_to_one`, `group`, `peer`, `mixed`, `unclear` |
| `purpose` | `youth_development` (general mentoring), `delinquency_prevention`, `reentry`, `career_workforce`, `academic`, `research_evaluation`, `training_technical_assistance`, `unclear` |
| `notes` | at most 15 words, own words |

## Quality control

- `scripts/validate.py` checks every output file: valid JSON, IDs match the batch, allowed
  values, word limits, and an **alignment check** (each record's notes must match its own
  title/abstract better than its neighbors', catching shifted rows).
- Agents keep temporary files in a private folder and build output by ID.
- **Reliability and calibration:** 8 of the NSF batches (320 awards) are tagged a second time,
  independently, by the reference (default) model; agreement and Cohen's kappa per field are
  reported (`output/tagging_reliability.csv`). The main pass uses Sonnet.
- Before external use, a person should check a random sample of tags against the abstracts.

## Privacy

NSF personal fields (PI and program officer names, emails, phones) are dropped at fetch time
and never stored. Award records describe organizations and projects, not participants.

## Changelog

- 1.0 (2026-11-19): initial protocol. Pilot on batch 3 (40 awards, Sonnet vs. reference model):
  kappa 0.79-1.00 on serves_youth, grade band, mentoring, bridging, AI/CS, setting and service
  geography.
- 1.0a (2026-11-19, analysis rule, no change to tagging): `evaluation` describes youth outcomes.
  The reference model set it to `none_stated` for awards that serve no youth, but the main pass
  did not. The analysis and the reliability check therefore read `evaluation` only for awards
  tagged as serving youth (directly or indirectly). Under that rule, pilot agreement is kappa
  0.74, and 100% on the yes/no question of a randomized or comparison-group design.
- 1.0b (analysis rule): NSF collaborative awards split one project across institutions and
  repeat the same abstract. Dollar totals sum the awards. Counts of "projects" group awards
  that share a title, after removing the "Collaborative Research:" prefix.
