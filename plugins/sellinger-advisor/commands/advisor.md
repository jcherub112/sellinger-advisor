---
description: Overview of Sellinger Advisor and its three tasks; routes you to the right one.
argument-hint: "[audit | check | lookup] (optional)"
---

Sellinger Advisor helps a Sellinger faculty advisor prepare for advising. It works from the bundled
2026-27 catalogue, program requirements, advising worksheets, policies, and the Spring 2027 section
snapshot, and it checks every plan with a deterministic validator. It is a planning aid: the advisor
approves everything.

If the user passed an argument, go straight to that task. Otherwise show this menu briefly and ask what
they have:

1. **Plan from an audit** (advise-audit). "Here is my advisee's DegreeWorks audit." Produces an advisor
   brief plus a student-ready plan, validated. Tip: put the PDF in a folder and give the path, so
   identifiers are stripped before Claude reads it.
2. **Check a plan** (check-plan). "My advisee wants FI 441 and OM 334 next spring." or "Check this plan
   another AI made." Returns errors with evidence and fixes.
3. **Quick lookup** (catalog-lookup). "When is FI 440 offered?" "What sections of AC 202 are open in
   Spring 2027?" "Can a first-year with a 2.8 take six courses?"

Data: 2026-27 undergraduate catalogue (pulled Oct 2026); Spring 2027 posted schedule (snapshot, Oct 2026).
Seats change daily: https://colss-prod.ec.loyola.edu/Student/Courses
