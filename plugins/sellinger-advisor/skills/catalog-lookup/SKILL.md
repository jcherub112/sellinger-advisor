---
name: catalog-lookup
description: "For a Sellinger faculty advisor: answer quick questions about Sellinger courses, programs and advising policy from the bundled 2026-27 catalogue data. Trigger on 'when is FI 440 offered', 'what are the prerequisites for', 'what sections of X are there in Spring 2027', 'what does the Finance major require', 'what electives count for', 'can a first-year with a 2.8 take six courses', 'which courses fit a real estate career', 'is there a course on'. Looks facts up with the bundled helper instead of answering from memory. For a full audit-based plan use advise-audit; to check a proposed schedule use check-plan."
---

# Catalogue and policy lookup

First read `../../references/advisor-rules.md`. The helper is `../../scripts/sa.py` relative to this file.

## How to answer
- **A specific course** (prerequisites, terms, credits, restrictions): `sa.py lookup <codes>`. Quote the
  catalogue's requisite text and "typically offered" wording. Note equivalents the helper returns.
- **Find a course by topic**: `sa.py search <words>`. Only name courses the search returns.
- **Sections and times**: `sa.py sections "Spring 2027" <codes>`. Only Spring 2027 is bundled; for other
  terms say so and point to Course Search. Seats in the snapshot are from Oct 2026.
- **Program requirements**: read the matching `data/01*` file, and `data/06_advising_worksheets.md` when
  the student's catalogue year matters.
- **Policy** (sixth course, Core, residency, standing, transfer, repeats): `data/03_policies_core_and_rules.md`.
  Sixth course: "eligible to REQUEST" or "not eligible to request", with the reason; never "approved".
- **Career fit for electives**: `data/04_career_pathways.txt`, labeled as context, not a requirement.
- **Professor ratings**: no data here; point to https://www.ratemyprofessors.com/school/876.

Keep answers short: the fact, its source file or catalogue text, and any "needs confirmation" caveat.
If the sources do not cover it, say so and point to https://catalogue.loyola.edu or the department.
No em dashes.
