#!/usr/bin/env python3
"""Deterministic checks for the Sellinger Advisor helper. Run: python3 tests/run_tests.py"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SA = os.path.join(ROOT, "plugins", "sellinger-advisor", "scripts", "sa.py")
FIX = os.path.join(ROOT, "tests", "fixtures", "FAKE_DegreeWorks_audit_Finance_Class2029.pdf")
OUT = os.path.join(ROOT, "tests", "out")
os.makedirs(OUT, exist_ok=True)
fails = 0


def run(*args):
    r = subprocess.run([sys.executable, SA, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout)
    return json.loads(r.stdout)


def check(name, cond, detail=""):
    global fails
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


info = run("info")
check("course master has 233 courses", info["courses_in_master"] == 233, info["courses_in_master"])

lk = {r["code"]: r for r in run("lookup", "FI 440", "FI 441", "RE 201", "IS 458")}
check("FI 440 is Fall", lk["FI 440"]["terms_offered"] == "Fall", lk["FI 440"].get("terms_offered"))
check("FI 441 Spring + senior-only", lk["FI 441"]["terms_offered"] == "Spring" and "seniors" in lk["FI 441"]["requisites_and_restrictions"])
check("RE 201 not found", lk["RE 201"]["found"] is False)
check("IS 458 is Spring", lk["IS 458"]["terms_offered"] == "Spring")

# T1-style plan (from TEST_SCRIPT T1): should pass with a sensible plan
hist = {"completed": ["AC 201", "EC 102", "EC 103", "MA 151", "IS 251", "EC 220", "FI 230", "FI 322", "MK 240", "OM 260"],
        "credits_earned": 75, "cum_gpa": 3.2}
plan = {"Spring 2027": ["MG 201", "LW 305", "FI 350"], "Fall 2027": ["FI 440"], "Spring 2028": ["FI 441"]}
v = run("validate", "--history", json.dumps(hist), "--plan", json.dumps(plan))
check("T1 good plan has 0 errors", v["errors"] == 0, v["flags"])

# T2: IS 458 and OM 334 in Fall 2027 should error
v2 = run("validate", "--history", json.dumps({"completed": ["IS 251", "OM 260"], "credits_earned": 60}),
         "--plan", json.dumps({"Fall 2027": ["IS 458", "OM 334"]}))
errs = [f for f in v2["flags"] if f["level"] == "ERROR"]
check("T2 IS 458 Fall flagged", any(f["course"] == "IS 458" and "Spring" in f["issue"] for f in errs), errs)
check("T2 OM 334 Fall flagged", any(f["course"] == "OM 334" and "Spring" in f["issue"] for f in errs), errs)

# T3: first-year, 2.8 GPA, six courses -> not eligible to request
v3 = run("validate", "--history", json.dumps({"completed": [], "credits_earned": 15, "cum_gpa": 2.8, "first_year": True}),
         "--plan", json.dumps({"Spring 2027": ["AC 201", "MA 151", "EC 102", "WR 100", "PL 201", "TH 201"]}))
check("T3 sixth course not eligible", any("Not eligible to request" in f["issue"] for f in v3["flags"]), v3["flags"])

# Section time conflict
cs = run("check-sections", "Spring 2027", "FI 441-02", "AC 201-01")
check("section conflict detected", any("TIME CONFLICT" in i for i in (cs["issues"] if isinstance(cs, dict) else cs)), cs)

# Sections unavailable for an unbundled term
s = run("sections", "Fall 2027", "FI 440")
check("Fall 2027 sections reported unavailable", s["available"] is False)

# Redaction on the fictional audit
red = os.path.join(OUT, "fake_REDACTED.txt")
r = run("redact", FIX, "--out", red)
text = open(red, encoding="utf-8").read()
check("redaction removed name, ID, email", all(k in r["removed"] for k in ("name", "ID number", "email")), r["removed"])
check("redacted text keeps courses", "MA 151" in text and "EC 220" in text)

print(f"\n{'ALL PASSED' if fails == 0 else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
