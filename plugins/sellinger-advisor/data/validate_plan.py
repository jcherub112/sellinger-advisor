"""
Sellinger Advising Tool - plan validator (run inside ChatGPT Code Interpreter or any Python 3).

USAGE (inside the GPT): build `history` and `plan`, then call validate().
    history = {"completed": ["AC 201","EC 102",...], "in_progress": ["FI 230",...],
               "registered": {"Spring 2027": ["FI 322", ...]},   # optional, already-registered future terms
               "credits_earned": 45, "cum_gpa": 3.1, "first_year": False, "scholar": False}
    plan = {"Spring 2027": ["FI 322","LW 305",...], "Fall 2027": [...], ...}   # chronological order not required
    report = validate(history, plan)   # returns list of flag dicts; also prints a table

If a posted section file exists for a term (07_sections_spring2027.csv), it overrides the catalog's
"typically offered" pattern for that term. check_sections(term, ["FI 441-01", ...]) lists days/times
and flags time conflicts.

Checks every planned course for: exists in 2026-27 catalog, offered that term, prerequisites met
by an EARLIER term (or same term where the catalog says 'may be taken concurrently'), credit-count
prerequisites, class-standing restrictions, already taken/duplicated, per-term load (5-course limit
-> sixth-course policy), and Fall/Spring-only bottlenecks.

It is a guardrail, not a registrar. Anything it can't parse is reported as NEEDS CONFIRMATION, never as OK.
"""
import csv, re, os

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
CANDIDATES = [os.path.join(HERE, "02_course_master_2026-27.csv"), "/mnt/data/02_course_master_2026-27.csv",
              "02_course_master_2026-27.csv"]

# Honors / legacy equivalents: satisfying one satisfies the other for prerequisite purposes.
EQUIV = [
    {"AC 201", "BH 200"}, {"MG 201", "BH 201"}, {"AC 202", "BH 202"},
    {"FI 230", "BH 230", "FI 320", "BH 320"}, {"MK 240", "BH 240"}, {"IS 251", "BH 251"},
    {"OM 260", "BH 260", "OM 330", "BH 330"}, {"IB 282", "BH 282"}, {"LW 305", "BH 305"},
    {"LW 406", "BH 406"}, {"EC 220", "ST 210"},
    {"FI 225", "REE 225"}, {"FI 300", "FRI 300"}, {"FI 305", "FRI 305"}, {"FI 325", "REE 325"},
    {"FI 335", "REE 335"}, {"IB 315", "MG 315"}, {"IB 300", "MG 300"}, {"IB 371", "MG 371"},
    {"IB 415", "MG 415"},
]
CODE_RE = re.compile(r"\b([A-Z]{2,3})\s?\*?\s?(\d{3})\b")


def norm(c):
    m = CODE_RE.search(c.upper())
    return f"{m.group(1)} {m.group(2)}" if m else c.strip().upper()


def expand(codes):
    s = set(norm(c) for c in codes)
    for grp in EQUIV:
        if s & grp:
            s |= grp
    return s


def load_catalog():
    for p in CANDIDATES:
        if os.path.exists(p):
            with open(p, newline="", encoding="utf-8") as f:
                return {r["code"]: r for r in csv.DictReader(f)}
    raise FileNotFoundError("02_course_master_2026-27.csv not found")


SCHED_DIRS = [HERE, "/mnt/data", "."]
BIZ = {"AC","BA","BH","DS","EC","FI","FRI","IB","IS","LW","MA","MG","MK","OM","REE","ST"}


def load_schedule(term):
    """Posted section schedule for a term, e.g. 'Spring 2027' -> 07_sections_spring2027.csv, or None."""
    fn = "07_sections_" + re.sub(r"\s+", "", term.lower()) + ".csv"
    for d in SCHED_DIRS:
        p = os.path.join(d, fn)
        if os.path.exists(p):
            with open(p, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            sched = {}
            for r in rows:
                sched.setdefault(r["course"], []).append(r)
            return sched
    return None


def _mins(t):
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", t.strip(), re.I)
    if not m: return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    return (h % 12 + (12 if ap == "PM" else 0)) * 60 + mi


def _slots(r):
    out = []
    for d, a, b in zip(r["days"].split(" ; "), r["start"].split(" ; "), r["end"].split(" ; ")):
        s, e = _mins(a), _mins(b)
        if s is None or e is None: continue
        for day in d.split("/"):
            out.append((day.strip(), s, e))
    return out


def check_sections(term, picks, verbose=True):
    """picks = ["FI 441-01", "REE 225-01", ...]. Prints each section's days/times and any time conflicts."""
    sched = load_schedule(term)
    if not sched:
        print(f"No posted section file for {term}; cannot check times."); return []
    chosen, issues = [], []
    for p in picks:
        c, _, sec = p.replace("*", " ").partition("-")
        c = norm(c); sec = sec.strip()
        rows = [r for r in sched.get(c, []) if not sec or r["section"] == sec]
        if not rows:
            issues.append(f"[ERROR] {p}: not on the posted {term} schedule."); continue
        r = rows[0]; chosen.append((p, r))
        if verbose:
            print(f"{p}: {r['days']} {r['start']}-{r['end']} | {r['room']} | {r['instructor']} | seats {r['seats_available']}/{r['capacity']} {r['status']}")
    for i in range(len(chosen)):
        for j in range(i + 1, len(chosen)):
            for d1, s1, e1 in _slots(chosen[i][1]):
                for d2, s2, e2 in _slots(chosen[j][1]):
                    if d1 == d2 and s1 < e2 and s2 < e1:
                        issues.append(f"[ERROR] TIME CONFLICT: {chosen[i][0]} and {chosen[j][0]} overlap on {d1}.")
    for x in dict.fromkeys(issues): print(x)
    if verbose and not issues: print("SECTIONS: no time conflicts.")
    return issues


def term_season(term):
    t = term.lower()
    for s in ("fall", "spring", "summer", "winter"):
        if s in t:
            return s.capitalize()
    return "?"


def term_key(term):
    yr = re.search(r"(20\d\d)", term)
    order = {"Spring": 1, "Summer": 2, "Fall": 3, "Winter": 0}
    return (int(yr.group(1)) if yr else 9999, order.get(term_season(term), 5))


def parse_reqs(text):
    """Return (hard_groups, concurrent_groups, credits_needed, soft_flag).
    groups = list of OR-sets; every group must be satisfied."""
    hard, conc, credits, soft = [], [], 0, False
    if not text:
        return hard, conc, credits, soft
    # split into segments by label
    segs = re.split(r"(Prerequisite \(may be taken concurrently\):|Concurrent Requisite:|Recommended Prerequisite:|Prerequisites?:|Requisite:|Restrictions?:)", text)
    label = None
    for s in segs:
        if s.endswith(":") and s.strip() in ("Prerequisite (may be taken concurrently):", "Concurrent Requisite:",
                                              "Recommended Prerequisite:", "Prerequisite:", "Prerequisites:",
                                              "Requisite:", "Restriction:", "Restrictions:"):
            label = s.strip(); continue
        if not label or label.startswith("Restriction") or label.startswith("Recommended"):
            continue
        body = s.strip().rstrip(".")
        if re.search(r"permission|varies|ALEKS|high school|grade of", body, re.I):
            soft = True
        m = re.search(r"(\d{2,3})\s+credits", body)
        if m:
            credits = max(credits, int(m.group(1)))
        target = conc if ("concurrent" in label.lower()) else hard
        for clause in re.split(r";|,(?![^()]*\))|\band\b", body):
            codes = [f"{a} {b}" for a, b in CODE_RE.findall(clause)]
            if codes:
                target.append(set(codes))
    return hard, conc, credits, soft


def standing_needed(restr):
    r = (restr or "").lower()
    if "restricted to seniors" in r or "restricted to senior" in r:
        return 90, "senior"
    if "juniors or seniors" in r or "juniors and seniors" in r or "junior and senior" in r:
        return 60, "junior"
    if "sophomores, juniors" in r or "sophomore, junior" in r:
        return 30, "sophomore"
    return 0, ""


def validate(history, plan, verbose=True):
    cat = load_catalog()
    done = expand(history.get("completed", []) + history.get("in_progress", []))
    credits = float(history.get("credits_earned", 0)) + 3 * len(history.get("in_progress", []))
    terms = dict(history.get("registered", {}))
    for t, cs in plan.items():
        terms.setdefault(t, [])
        terms[t] = list(dict.fromkeys(terms[t] + cs))
    flags, seen = [], set(done)
    registered = {t: set(norm(c) for c in cs) for t, cs in history.get("registered", {}).items()}

    def flag(level, term, course, msg):
        flags.append({"level": level, "term": term, "course": course, "issue": msg})

    for term in sorted(terms, key=term_key):
        courses = [norm(c) for c in terms[term]]
        season = term_season(term)
        this_term = expand(courses)
        sched = load_schedule(term)
        term_credits, n_full = 0.0, 0
        for c in courses:
            row = cat.get(c)
            is_reg = c in registered.get(term, set())
            if c in seen and c not in ("FI 426", "MK 449", "IS 452", "EC 341", "LW 409", "MG 419", "REE 426", "FRI 426"):
                flag("ERROR", term, c, "Already completed / in progress / planned earlier (possible duplicate).")
            if not row:
                biz = c.split()[0] in {"AC","BA","BH","EC","FI","FRI","IB","IS","LW","MG","MK","OM","REE","ST","MA","DS"}
                if biz:
                    flag("CONFIRM", term, c, "Business/math course not in the 2026-27 course master (legacy number or typo?). Verify in live course search.")
                else:
                    flag("INFO", term, c, "Core/non-business course - offering and prerequisites not checked by this tool.")
                term_credits += 3; n_full += 1
                continue
            cr = row["credits"]
            crv = float(cr.split("-")[-1]) if re.match(r"^[\d.]+(-[\d.]+)?$", cr) else 3.0
            term_credits += crv
            if crv >= 3:
                n_full += 1
            offered = row["terms_offered"]
            if sched is not None and c.split()[0] in BIZ:
                on = [k for k in expand([c]) if k in sched]
                if on:
                    secs = sum(len(sched[k]) for k in on)
                    flag("OK", term, c, f"On the posted {term} schedule ({secs} section(s)).")
                elif not is_reg:
                    flag("ERROR", term, c, f"NOT on the posted {term} schedule - pick another course or confirm with the department.")
            elif season in ("Fall", "Spring", "Summer") and offered and offered != "Varies" and season not in offered:
                flag("ERROR", term, c, f"Not normally offered in {season} (catalog: {offered}).")
            elif offered in ("Varies", "") or row["frequency"] in ("Varies", "Not stated", "Even Years", "Odd Years"):
                flag("CONFIRM", term, c, f"Offering pattern is '{offered or 'not stated'} / {row['frequency']}' - verify the live schedule.")
            hard, conc, need_cr, soft = parse_reqs(row["requisites_and_restrictions"])
            for grp in hard:
                if not (expand(grp) & seen):
                    flag("ERROR", term, c, f"Prerequisite not met before this term: needs one of {sorted(grp)}.")
            for grp in conc:
                if not (expand(grp) & (seen | this_term)):
                    flag("ERROR", term, c, f"Needs (earlier or same term): one of {sorted(grp)}.")
            if need_cr and credits < need_cr:
                flag("ERROR", term, c, f"Requires {need_cr} credits; student projected at {credits:.0f} at start of {term}.")
            min_cr, lab = standing_needed(row["requisites_and_restrictions"])
            if min_cr and credits < min_cr:
                flag("WARN", term, c, f"Restricted to {lab}+ standing; projected credits {credits:.0f} (<{min_cr}). Confirm class standing.")
            if re.search(r"restricted to .*majors|scholars|minors", row["requisites_and_restrictions"], re.I):
                flag("CONFIRM", term, c, "Has a major/program restriction: " + row["requisites_and_restrictions"][:160])
            if soft:
                flag("CONFIRM", term, c, "Requisite includes permission/equivalency/placement language - confirm eligibility.")
            if is_reg:
                pass
        if season in ("Fall", "Spring"):
            if n_full > 6:
                flag("ERROR", term, "-", f"{n_full} full courses: exceeds the hard cap of six 3/4-credit courses.")
            elif n_full == 6:
                gpa = history.get("cum_gpa")
                fy = history.get("first_year")
                if gpa is None:
                    flag("WARN", term, "-", "Sixth course planned: student may REQUEST it (advisor approval required). GPA unknown - eligibility not verified.")
                elif fy and gpa < 3.0:
                    flag("ERROR", term, "-", f"Sixth course planned but first-year students need a 3.000 first-semester QPA (have {gpa}). Not eligible to request.")
                elif (not fy) and gpa < 2.0:
                    flag("ERROR", term, "-", f"Sixth course planned but upperclassmen need good standing (2.000+); GPA {gpa}. Not eligible to request.")
                else:
                    flag("WARN", term, "-", "Sixth course planned: student is ELIGIBLE TO REQUEST it; advisor must grant electronic permission. Not approved by this tool.")
            if term_credits < 12:
                flag("WARN", term, "-", f"Only {term_credits:.0f} credits - below full-time (12). Scholars need 12+ (director approval otherwise).")
            if term_credits >= 19:
                flag("WARN", term, "-", f"{term_credits:.0f} credits - heavy load.")
        seen |= this_term
        credits += term_credits
    if verbose:
        if not flags:
            print("VALIDATION PASSED: no issues found (still subject to advisor confirmation).")
        for f in flags:
            if f["level"] in ("INFO", "OK"): continue
            print(f"[{f['level']}] {f['term']} | {f['course']} | {f['issue']}")
        n_info = sum(1 for f in flags if f["level"] == "INFO")
        errs = sum(1 for f in flags if f["level"] == "ERROR")
        if n_info: print(f"[INFO] {n_info} Core/non-business course(s) not checked (verify in course search).")
        print(f"SUMMARY: {errs} error(s), {sum(1 for f in flags if f['level'] in ('WARN','CONFIRM'))} warning/confirmation item(s).")
        print(f"Projected total credits after plan: {credits:.0f} (120 minimum, 38 courses minimum).")
    return flags


if __name__ == "__main__":
    demo_hist = {"completed": ["AC 201", "EC 102", "EC 103", "MA 151", "IS 251", "EC 220", "FI 230"],
                 "in_progress": ["MK 240", "FI 322"], "credits_earned": 45, "cum_gpa": 3.2}
    demo_plan = {"Spring 2027": ["FI 350", "LW 305", "OM 260", "OM 334", "FI 441"],
                 "Fall 2027": ["FI 440", "FI 430", "IS 458", "MG 201", "FI 431", "FI 433"]}
    validate(demo_hist, demo_plan)
