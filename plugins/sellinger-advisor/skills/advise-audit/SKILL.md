---
name: advise-audit
description: "For a Sellinger faculty advisor: turn a student's DegreeWorks audit (PDF or text) into a validated graduation plan plus an advisor brief. Trigger on 'review this audit', 'plan this advisee', 'build a plan from this DegreeWorks', 'what does this student still need', 'prep me for my advising meeting', or when an advisor hands over a DegreeWorks file. Redacts identifiers first, reads the audit, plans remaining terms, runs the bundled validator and section-conflict check, and writes an advisor brief followed by a student-ready plan the advisor can forward. For checking a plan someone else made use check-plan; for a quick course or policy question use catalog-lookup."
---

# Advise from a DegreeWorks audit

First read `../../references/advisor-rules.md` (plugin-root/references). It governs sources, privacy,
validation and style. Then read `../../data/00_report_template_and_workflow.md` for the report template
and the known data cautions. The helper is `../../scripts/sa.py` relative to this file.

## Steps (in order, every time)
1. **Get a redacted copy.** If you have a file path, run
   `python3 <plugin-root>/scripts/sa.py redact "<path>" --name "<student name, only if the advisor gave it>"`
   and read only the `_REDACTED.txt` it writes. Scan it for leftover identifiers. If the PDF was
   attached to the chat instead, follow the attached-file rule in advisor-rules.md.
2. **Read the audit.** Record catalogue year, degree, major(s), minor(s), Scholars/Honors, credits
   earned, GPA if shown, class standing, and every course as Completed / In Progress / Registered /
   Still Needed. Keep the audit's own buckets, substitutions, waivers and double-counts.
3. **Load the rules** for this student's programs from the matching `data/01*` file(s) and the matching
   catalogue-year worksheet in `data/06_advising_worksheets.md`. Policy from `data/03`.
4. **Check course facts** with `sa.py lookup` for every course you will place or discuss.
5. **Build the plan** for remaining requirements only (ordering rules in advisor-rules.md). If the
   advisor named a goal (study abroad term, minor, graduation term), honor it or say why not.
6. **Validate.** Run `sa.py validate` with the history and plan. Fix every ERROR and re-run. For Spring
   2027 choose sections with `sa.py sections` and run `sa.py check-sections`; fix conflicts.
7. **Write the output** (below). If the advisor wants a file, save it as markdown (or .docx if asked)
   under a neutral name the advisor picks, never the student's name.

## Output
### Part A: Advisor brief (for the advisor only; first, concise)
- One line: program(s), catalogue year, credits, standing, projected graduation term (or "not
  determinable from the audit").
- **Validator result:** the exact `summary_line`, plus each remaining CONFIRM/WARN in one line.
- **Decisions for you:** sixth-course request eligibility, substitutions or waivers to approve,
  catalogue-year questions, anything blocked.
- **Audit discrepancies**, **double-counting assumptions**, **sequencing risks** (Fall/Spring-only
  chains, capstone timing, senior restrictions), **data uncertainties** (legacy numbers, "Varies"
  offerings, catalogue-year mismatches).
- **Talking points** for the meeting: 3 to 5 bullets.

### Part B: Student-ready plan (the advisor may forward or edit it)
Use the template in `data/00_report_template_and_workflow.md`, sections 1 to 7, in plain, warm,
student-friendly language. Omit the "Flags for the Advisor" block there (Part A replaces it). End with:
"This is a planning aid, not your official audit. Confirm with your advisor before registering.
Offerings and seats change every term." No em dashes.

## Do not
- Do not approve anything, promise seats, or state a course fact you did not look up.
- Do not re-plan completed, in-progress or registered courses unless the advisor asks.
- Do not claim the validator passed unless its output says so.
