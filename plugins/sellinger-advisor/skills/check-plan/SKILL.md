---
name: check-plan
description: "For a Sellinger faculty advisor: check a course plan or schedule that a student, another advisor, or another AI tool produced. Trigger on 'check this plan', 'is this schedule OK', 'my advisee wants to take X and Y in the fall', 'did this AI plan get it right', 'can this student take FI 441 next spring', 'any time conflicts in these sections'. Runs the bundled validator and section-conflict check against the 2026-27 catalogue and returns errors with evidence and concrete fixes. For a full plan built from a DegreeWorks audit use advise-audit; for a single course or policy question use catalog-lookup."
---

# Check a proposed plan

First read `../../references/advisor-rules.md`. The helper is `../../scripts/sa.py` relative to this file.

## Steps
1. **Separate claims from facts.** List what the plan proposes (terms, courses, sections) and what it
   asserts (e.g. "FI 440 is offered in spring"). Do not accept any assertion until checked.
2. **Get the student's history.** Use what the advisor gives (completed, in progress, registered,
   credits, GPA, first-year or not). If a DegreeWorks audit is provided, redact and read it as in
   advisor-rules.md. If history is missing, ask once for the minimum needed (completed courses and
   credits); if the advisor cannot supply it, run with what you have and say which checks are weaker.
3. **Look up every course** with `sa.py lookup`. Unknown numbers: say they are not in the 2026-27
   master and do not substitute a guess.
4. **Validate** with `sa.py validate`. For Spring 2027 sections, run `sa.py check-sections`.
5. **Propose fixes** for each ERROR: a concrete swap or re-sequencing, then re-run the validator on the
   fixed version and report both results.

## Output
- **Verdict** in one line: the validator's `summary_line` for the plan as given.
- **Errors** table: Term | Course | Problem | Evidence (catalogue text or validator flag) | Fix.
- **Needs confirmation** list (CONFIRM/WARN items).
- **Fixed plan** (if any ERRORs) with its own validator `summary_line`.
- If the plan came from another AI: one line on what it got right and what it invented.
No em dashes. Never say a plan is approved.
