# Sellinger Advisor

A Claude plugin for faculty advisors in Loyola University Maryland's Sellinger School of Business.
It turns a student's DegreeWorks audit into a checked graduation plan and an advisor brief, checks
schedules students bring in, and answers course, section and policy questions from the 2026-27
catalogue. It is a planning aid. The advisor approves everything.

## What it does

| Task | You say | You get |
|---|---|---|
| Plan from an audit | "Here's my advisee's DegreeWorks audit: /path/audit.pdf" | An advisor brief (validator result, decisions for you, risks, talking points) plus a student-ready plan you can forward |
| Check a plan | "My advisee wants IS 458 and OM 334 next fall. OK?" | Errors with catalogue evidence, fixes, and a re-validated plan |
| Quick lookup | "When is FI 440 offered?" "Spring 2027 sections of AC 202?" "Can a first-year with a 2.8 take six?" | The answer, with its source |

Type `/advisor` for the menu.

Every plan is checked by a deterministic validator (`validate_plan.py`, unchanged from the advising GPT
v3) for offering terms, prerequisites, credit and standing requirements, duplicates and the
sixth-course policy. Spring 2027 sections are checked for time conflicts.

## Install

Claude desktop app: open the Plugins page (under Customize), choose **Add marketplace**, enter
`jcherub112/sellinger-advisor`, then install **sellinger-advisor**. Start a new chat and type `/advisor`.

Claude Code:

```
claude plugin marketplace add jcherub112/sellinger-advisor
claude plugin install sellinger-advisor@sellinger-advisor
```

## Privacy

Give Claude the audit as a file path (for example, a PDF in a connected folder) rather than attaching it
to the chat. The plugin then strips the student's name, Loyola ID, email, phone and date of birth before
Claude reads it (`scripts/sa.py redact`). Redaction is a safeguard, not a compliance guarantee. Follow
Loyola's guidance on using AI tools with student records.

## Data

- 2026-27 undergraduate catalogue: 233-course master, program requirements, advising worksheets,
  policies (pulled Oct 2026)
- Spring 2027 posted schedule (snapshot Oct 2026; seats change daily)

Updating: replace files in `plugins/sellinger-advisor/data/` (a new term's sections go in
`07_sections_<term>.csv`, e.g. `07_sections_fall2027.csv`), bump `version` in both
`.claude-plugin/marketplace.json` and `plugins/sellinger-advisor/.claude-plugin/plugin.json`, push.
Users update with `claude plugin marketplace update sellinger-advisor` then
`claude plugin update sellinger-advisor@sellinger-advisor`, or Update on the Plugins page.

## Tests

`python3 tests/run_tests.py` runs the deterministic checks (lookups, validator cases, section
conflicts, redaction on a fictional audit).

## License

MIT. See `LICENSE`. Copyright (c) 2026 Jason Cherubini.
