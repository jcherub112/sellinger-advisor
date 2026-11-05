# Sample run on the FICTIONAL test audit (not a real student)

Run 2026-11-05 by Claude following the advise-audit skill steps by hand with the bundled helper
(a fully unattended headless run was not possible in the build environment).

1. `sa.py redact` on FAKE_DegreeWorks_audit_Finance_Class2029.pdf (pdftotext): removed 1 name, 1 ID number, 1 email.
2. Audit read: Finance BS, catalogue year 2025-2026, 39 credits applied, GPA 3.24, 5 courses in progress Fall 2026.
3. First plan put FI 330 in Spring 2027. Validator: NOT passed, 1 error ("FI 330 NOT on the posted Spring 2027
   schedule"), 1 confirmation (FI 330 restricted to sophomore finance majors).
4. Swapped FI 330 for FI 340 (Fall;Spring per catalogue). Validator: passed, 0 error(s), 0 confirmation(s).
   Core and free-elective slots were left as placeholders (CORE ETHICS, FREE ELECTIVE-1, ...), which the
   validator reports as INFO, not checked.
5. Spring 2027 sections: first picks MG 201-01 + OM 260-01 conflicted (both T/Th 9:25 AM). Final picks
   MG 201-01, OM 260-02, FI 350-01, FI 340-01: no time conflicts.

Final plan tested:
| Term | Courses |
|---|---|
| Spring 2027 | MG 201, OM 260, FI 350, FI 340, Core second PL/TH |
| Fall 2027 | LW 305, FI 430, FI 431, Core ethics, Core natural science |
| Spring 2028 | FI 380, FI 433, Core fine arts, Core DJ, free elective |
| Fall 2028 | FI 440, Core DJ, 3 free electives |
| Spring 2029 | FI 441, 4 free electives |
