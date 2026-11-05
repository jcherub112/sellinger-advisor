#!/usr/bin/env python3
"""
Sellinger Advisor helper. Stdlib only. Wraps the bundled data and validator so the
skills never state a course fact from memory.

Subcommands (run with python3 sa.py <cmd> ...):
  lookup CODE [CODE ...]            Catalog rows for course codes (equivalents noted).
  search WORDS                      Keyword search over code, title, description.
  sections TERM CODE [CODE ...]     Posted sections for a term (only Spring 2027 is bundled).
  validate --history H --plan P     Run validate_plan.validate. H and P are JSON strings or .json paths.
  check-sections TERM PICK [PICK ...]  Time-conflict check, picks like "FI 441-01".
  redact FILE [--name "First Last"] [--out OUT]
                                    Extract text from a DegreeWorks PDF or .txt and strip
                                    name, Loyola ID, email, phone and date of birth.
  info                              Data versions and counts.

Every command prints JSON (validate also prints the human-readable table to stderr).
"""
import argparse, contextlib, csv, io, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
sys.path.insert(0, DATA)
import validate_plan as V  # noqa: E402  (the original v3 validator, unchanged)

CATALOG_CSV = os.path.join(DATA, "02_course_master_2026-27.csv")


def catalog():
    with open(CATALOG_CSV, newline="", encoding="utf-8") as f:
        return {r["code"]: r for r in csv.DictReader(f)}


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def load_json_arg(s):
    if s is None:
        return None
    if os.path.exists(s):
        with open(s, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(s)


def cmd_lookup(a):
    cat = catalog()
    res = []
    for raw in a.codes_joined():
        c = V.norm(raw)
        row = cat.get(c)
        equiv = sorted(V.expand([c]) - {c})
        if row:
            res.append({"code": c, "found": True, "equivalents": equiv, **row})
        else:
            alt = [e for e in equiv if e in cat]
            res.append({"code": c, "found": False, "equivalents": equiv,
                        "note": ("Not in the 2026-27 course master. " +
                                 (f"Equivalent(s) in the master: {', '.join(alt)}." if alt else
                                  "Do not suggest this number; it may be legacy, Core/non-business, or a typo."))})
    out(res)


def cmd_search(a):
    words = [w.lower() for w in a.words]
    hits = []
    for code, r in catalog().items():
        blob = " ".join([code, r.get("title", ""), r.get("description_short", "")]).lower()
        if all(w in blob for w in words):
            hits.append({k: r[k] for k in ("code", "title", "credits", "terms_offered", "frequency",
                                            "requisites_and_restrictions")})
    out({"query": " ".join(a.words), "count": len(hits), "results": hits[: a.limit]})


def cmd_sections(a):
    sched = V.load_schedule(a.term)
    if sched is None:
        out({"term": a.term, "available": False,
             "note": f"No posted section file for {a.term}. Only Spring 2027 is bundled. "
                     "Point to live Course Search: https://colss-prod.ec.loyola.edu/Student/Courses"})
        return
    res = {}
    for raw in a.codes_joined():
        c = V.norm(raw)
        rows = []
        for k in sorted(V.expand([c])):
            rows += sched.get(k, [])
        res[c] = rows
    out({"term": a.term, "available": True,
         "note": "Snapshot of the posted schedule (Oct 2026). Seats change daily.", "sections": res})


def cmd_validate(a):
    hist = load_json_arg(a.history) or {}
    plan = load_json_arg(a.plan) or {}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        flags = V.validate(hist, plan, verbose=True)
    sys.stderr.write(buf.getvalue())
    errors = sum(1 for f in flags if f["level"] == "ERROR")
    confirms = sum(1 for f in flags if f["level"] in ("WARN", "CONFIRM"))
    out({"passed": errors == 0, "errors": errors, "confirmations": confirms,
         "summary_line": f"Validator: {'passed' if errors == 0 else 'NOT passed'}, {errors} error(s), {confirms} confirmation(s)",
         "flags": [f for f in flags if f["level"] != "OK"]})


def cmd_check_sections(a):
    picks = a.codes_joined()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = V.check_sections(a.term, picks, verbose=True)
    sys.stderr.write(buf.getvalue())
    out(r)


# ---------- redaction (port of the Advising Planner page's in-browser redact) ----------
def redact_text(text, name=None):
    hits = {}

    def sub(pattern, label, repl=None, flags=0):
        nonlocal text

        def _r(m):
            hits[label] = hits.get(label, 0) + 1
            return repl(m) if repl else f"[{label} removed]"
        text = re.sub(pattern, _r, text, flags=flags)

    if name and name.strip():
        for p in re.split(r"[\s,]+", name.strip()):
            if len(re.sub(r"\W", "", p)) >= 2:
                sub(r"\b" + re.escape(p) + r"\b", "name", flags=re.I)
    sub(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", "email", flags=re.I)
    sub(r"^([^\n]*?\b(?:date of birth|birth ?date|DOB|born)\b)[^\n]*", "date of birth",
        lambda m: m.group(1) + " [date of birth removed]", flags=re.I | re.M)
    sub(r"\b(student(?:'s)?\s*name|name)(\s*[:\-]?\s+)([A-Z][A-Za-z'\-]+(?:,)?(?: [A-Z][A-Za-z'.\-]*){1,3})",
        "name", lambda m: m.group(1) + m.group(2) + "[name removed]")
    sub(r"\(?\b\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}\b", "phone")
    sub(r"\b\d{6,10}\b", "ID number")
    sub(r"\b[A-Z]\d{7,9}\b", "ID number")
    return text, hits


def pdf_text(path):
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout, "pdftotext"
    for mod in ("pypdf", "PyPDF2"):
        try:
            lib = __import__(mod)
            rd = lib.PdfReader(path)
            return "\n".join((p.extract_text() or "") for p in rd.pages), mod
        except Exception:
            continue
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages), "pdfplumber"
    except Exception:
        pass
    raise SystemExit(json.dumps({"ok": False, "error":
        "No PDF text extractor available (pdftotext, pypdf, or pdfplumber). "
        "Install one (pip install pypdf) or save the DegreeWorks audit as text and pass the .txt."}))


def cmd_redact(a):
    if a.file.lower().endswith(".pdf"):
        raw, how = pdf_text(a.file)
    else:
        with open(a.file, encoding="utf-8", errors="replace") as f:
            raw, how = f.read(), "text"
    clean, hits = redact_text(raw, a.name)
    outp = a.out or re.sub(r"\.[^.]+$", "", a.file) + "_REDACTED.txt"
    with open(outp, "w", encoding="utf-8") as f:
        f.write(clean)
    out({"ok": True, "extractor": how, "redacted_file": outp, "removed": hits,
         "chars": len(clean),
         "next": "Read ONLY the redacted file. Scan it for any remaining identifiers before using it."})


def cmd_info(a):
    cat = catalog()
    files = sorted(os.listdir(DATA))
    out({"data_dir": DATA, "courses_in_master": len(cat), "files": files,
         "catalogue": "2026-27 undergraduate catalogue (pulled Oct 2026)",
         "sections": "Spring 2027 posted schedule snapshot (Oct 2026)"})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    def codes(p, name="codes"):
        p.add_argument(name, nargs="+")

    p = sp.add_parser("lookup"); codes(p); p.set_defaults(fn=cmd_lookup)
    p = sp.add_parser("search"); p.add_argument("words", nargs="+"); p.add_argument("--limit", type=int, default=25); p.set_defaults(fn=cmd_search)
    p = sp.add_parser("sections"); p.add_argument("term"); codes(p); p.set_defaults(fn=cmd_sections)
    p = sp.add_parser("validate"); p.add_argument("--history", required=True); p.add_argument("--plan", required=True); p.set_defaults(fn=cmd_validate)
    p = sp.add_parser("check-sections"); p.add_argument("term"); codes(p); p.set_defaults(fn=cmd_check_sections)
    p = sp.add_parser("redact"); p.add_argument("file"); p.add_argument("--name"); p.add_argument("--out"); p.set_defaults(fn=cmd_redact)
    p = sp.add_parser("info"); p.set_defaults(fn=cmd_info)
    a = ap.parse_args()

    # Rejoin tokens like "FI" "440" "FI" "441" or "FI 441-01" passed unquoted.
    def codes_joined():
        toks = getattr(a, "codes", [])
        joined, i = [], 0
        while i < len(toks):
            t = toks[i]
            if re.fullmatch(r"[A-Za-z]{2,3}", t) and i + 1 < len(toks) and re.match(r"\d{3}", toks[i + 1]):
                joined.append(f"{t} {toks[i + 1]}"); i += 2
            else:
                joined.append(t); i += 1
        return joined
    a.codes_joined = codes_joined
    a.fn(a)


if __name__ == "__main__":
    main()
