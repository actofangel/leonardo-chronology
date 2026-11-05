"""Markdown reports over the corpus and the Elements, for GitHub Actions job summaries and issue replies.

    python ops.py verify                 every check of every part (exit status 1 if any fails)
    python ops.py list                   the parts, by tradition
    python ops.py part euclid-II-11      one part: layers, checks, GeoGebra, Python
    python ops.py prop I.47              one Elements record: English, Greek, citations, formal proofs
    python ops.py search gnomon          Elements records whose English contains the text
    python ops.py archimedes             Archimedes proposition by proposition, every check
    python ops.py auctores               the other authors (Euclid's minor works, Apollonius, Ptolemy, Pappus, ...)
    python ops.py arch SC.I.33           one proposition (Archimedes or the others): enunciation, Greek, checks
    python ops.py works                  the Greek texts beyond the Elements (Archimedes, Apollonius, Pappus, ...)
    python ops.py text archimedes.dimensio-circuli 3     one Greek passage
    python ops.py greek μέναιχμ          search the Greek texts (accents and case ignored)
    python ops.py ask "prop I.47"        parse a free request (used by the issue workflow)

Output is Markdown on stdout.
"""
import inspect
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
PARTS = json.loads((ROOT / "parts.json").read_text())
TRAD = {t["key"]: t for t in PARTS["traditions"]}
BYID = {p["id"]: p for p in PARTS["parts"]}
LIMIT = 60000  # stay under the 65536 character limit of an issue comment


def fence(text, lang=""):
    text = text.rstrip("\n")
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}{lang}\n{text}\n{ticks}"


def verify():
    import geometria
    rows, bad = [], 0
    for pid in geometria.PARTS:
        _, checks = geometria.run(pid)
        for label, ch in checks:
            bad += not ch.ok
            rows.append(f"| {'✅' if ch.ok else '❌'} | `{pid}` | {ch.method} | {label} |")
    head = f"## Corpus Geometriae: verification\n\n**{len(geometria.PARTS)} parts, {len(rows)} checks, " + \
           ("all passed**" if not bad else f"{bad} FAILED**")
    note = ("\n\n`symbolic` holds identically in general symbols; `instance` holds exactly for one construction; "
            "`numeric` is confirmed to 50 digits and is not a proof.")
    return head + note + "\n\n| | part | method | check |\n|---|---|---|---|\n" + "\n".join(rows), bad


def listing():
    out = ["## Corpus Geometriae: parts\n"]
    for t in PARTS["traditions"]:
        ps = [p for p in PARTS["parts"] if p["tradition"] == t["key"]]
        if ps:
            out.append(f"**{t['name']}** ({t['date']})\n")
            out += [f"* `{p['id']}`: {p['title']} ({p['locus']})" for p in ps]
            out.append("")
    out.append("Ask for one with `part <id>`.")
    return "\n".join(out)


def part(pid):
    p = BYID.get(pid)
    if not p:
        near = [k for k in BYID if pid.lower() in k.lower()]
        return f"No part `{pid}`." + (f" Did you mean {', '.join(f'`{k}`' for k in near)}?" if near else " Try `list`.")
    t = TRAD[p["tradition"]]
    out = [f"## {p['title']}", f"*{t['name']}, {t['date']}* · **{p['locus']}** · citation {'located' if p['status'] == 'fixed' else 'to verify'}",
           f"Edition: {t['edition']}", "",
           f"**Fact** (what the source states, in summary): {p['fact']}", "",
           f"**Interpretation**: {p['interp']}"]
    if p.get("hypo"):
        out += ["", f"> **Working hypothesis, not evidence**: {p['hypo']}"]
    out += ["", "### Checks (recomputed now)"]
    try:
        import geometria
        _, checks = geometria.run(pid)
        out += [f"* {'✅' if ch.ok else '❌'} `{ch.method}` {label}" for label, ch in checks]
    except Exception as exc:  # report, do not hide
        out.append(f"Could not run: `{exc!r}`")
    try:
        import graeca as G
        src = G.sources(pid)
    except Exception:
        src = []
    if src:
        out += ["", "### Greek source text"]
        for wid, locus, note in src:
            w = G.work(wid)
            flag = " · **OCR, collate with the printed page before citing**" if w["transmission"] == "ocr" else ""
            body = G.text(wid, locus)
            out.append(f"<details><summary>{w['author']}, {w['title']}, {locus}{flag}</summary>\n\n"
                       + (f"*{note}*\n\n" if note else "") + "> " + body[:3000] + ("…" if len(body) > 3000 else "")
                       + f"\n\n{w['edition'][:200]}. [{w['source']['repo']}]({w['source']['url']})\n</details>")
    out += ["", "### GeoGebra (paste into the Input Bar)", fence(p["ggb"])]
    if p.get("note"):
        out.append(f"*{p['note']}*")
    out += ["", "### Python (`geometria.py`)", fence(p["python"], "python")]
    m = p.get("machine")
    if m:
        out += ["", f"### Machine proof: {m['engine']} ({'proved' if m['proved'] else 'not proved'})", m["note"],
                "<details><summary>proof</summary>\n\n" + fence(m["proof"]) + "\n</details>"]
    for f in p.get("formal") or []:
        out += ["", f"**{f['name']}** ({f['system']}, {f['license']}): [`{f['path']}`]({f['url']})", fence(f["statement"])]
    if p.get("elem"):
        out += ["", f"Full text of Elements {p['elem']}: `prop {p['elem']}`."]
    return "\n".join(out)


def prop(rid):
    import elementa as E
    rid = normalise(rid)
    if rid not in E.RECORDS:
        return f"No record `{rid}`. Ids look like `I.47`, `XIII.18`, `I.def.15`, `I.post.5`, `I.cn.1`, `X.def.2.3`."
    r = E.get(rid)
    out = [f"## Elements {rid}", f"*Book {r['book']}, {r['kind']}*", "",
           "**Heath (1908)**", "", "> " + r["enunciation"].replace("\n", "\n> "), ""]
    out += ["**Heiberg (1883 to 1888)**", "", "> " + r["greek"].replace("\n", "\n> ")] if r["greek"] else \
           ["*No separate Greek text for this record in the Perseus encoding.*"]
    if r["proof"]:
        out += ["", "<details><summary>Heath's proof</summary>\n\n" + r["proof"] + "\n</details>"]
    found = E.foundations(rid)
    out += ["", "### Citations (Heath's apparatus: interpretive layer, Euclid's text cites nothing)",
            f"* cites: {', '.join(f'`{c}`' for c in r['cites']) or 'nothing'}",
            f"* cited by: {', '.join(f'`{c}`' for c in r['cited_by']) or 'nothing'}",
            f"* rests on {len(found)} records in all; postulates: {', '.join(E.foundations(rid, 'post')) or 'none'}",
            f"* rests on the parallel postulate: **{'yes' if E.uses_parallel_postulate(rid) else 'no'}**"]
    gc, ln = E.geocoq(rid), E.lean(rid)
    if gc or ln:
        out += ["", "### Formal proofs (copied into `geometry/formal/`)"]
        for stem, src in gc.items():
            out.append(f"<details><summary>GeoCoq <code>{stem}.v</code></summary>\n\n{fence(src, 'coq')}\n</details>")
        if ln:
            out.append(f"<details><summary>LeanEuclid <code>Prop{int(r['lean']):02d}.lean</code></summary>\n\n{fence(ln, 'lean')}\n</details>")
    parts = [p["id"] for p in PARTS["parts"] if p.get("elem") == rid]
    if parts:
        out += ["", "Constructed and verified as " + ", ".join(f"`part {k}`" for k in parts) + "."]
    return "\n".join(out)


def search(text):
    import elementa as E
    if not text.strip():
        return "Give some text to search for, for example `search gnomon`."
    hits = E.search(text)
    if not hits:
        return f"No record contains “{text}”."
    rows = [f"| `{k}` | {E.get(k)['enunciation'][:140].replace('|', '/')}{'…' if len(E.get(k)['enunciation']) > 140 else ''} |" for k in hits[:80]]
    more = f"\n\n…and {len(hits) - 80} more." if len(hits) > 80 else ""
    return f"## “{text}” in the Elements: {len(hits)} records\n\n| id | enunciation |\n|---|---|\n" + "\n".join(rows) + more


SUITES = [("archimedes", "Archimedes"), ("auctores", "Euclid's minor works, Apollonius, Aristarchus, Theodosius, Hero, Ptolemy, Pappus, Nicomachus, Theon")]


def _suite(name):
    import importlib
    return importlib.import_module(name)


def verify_suite(name, title):
    M = _suite(name)
    rows, bad, total = [], 0, 0
    for pid in M.PROPS:
        for label, ch in M.run(pid):
            total += 1
            bad += not ch.ok
            rows.append(f"| {'✅' if ch.ok else '❌'} | `{pid}` | {ch.method} | {label} |")
    head = (f"## {title}: {len(M.PROPS)} propositions, {total} checks, " + ("all passed" if not bad else f"**{bad} FAILED**")
            + "\n\nEach proposition first checks that the Greek numeral at its locus is the expected number, where the "
            "encoding writes one. The checks establish the stated results in modern terms, not the ancient proofs.")
    return head + "\n\n| | proposition | method | check |\n|---|---|---|---|\n" + "\n".join(rows), bad


def verify_archimedes():
    return verify_suite(*SUITES[0])


def suite_list(name, title):
    M = _suite(name)
    out = [f"## {title}: propositions with checks", "", "| id | work | locus | enunciation (summary) |", "|---|---|---|---|"]
    for pid, p in M.PROPS.items():
        out.append(f"| `{pid}` | {p['work']} | {p['locus']} | {p['statement'][:150].replace('|', '/')}{'…' if len(p['statement']) > 150 else ''} |")
    out.append("\nOne proposition with its Greek: `arch <id>`. Run every check: `verify`.")
    return "\n".join(out)


def archimedes_list():
    return suite_list(*SUITES[0])


def auctores_list():
    return suite_list(*SUITES[1])


def archimedes_prop(pid):
    pid = pid.strip()
    for name, title in SUITES:
        M = _suite(name)
        if pid in M.PROPS:
            break
    else:
        near = [k for name, _ in SUITES for k in _suite(name).PROPS if pid and pid.lower() in k.lower()]
        return f"No proposition `{pid}`." + (f" Did you mean {', '.join(f'`{k}`' for k in near)}?" if near else " Try `archimedes` or `auctores`.")
    p = M.PROPS[pid]
    out = [f"## {pid}", f"`{p['work']}` locus `{p['locus']}`", "", f"**Enunciation** (summary of the Greek): {p['statement']}"]
    if p["note"]:
        out += ["", f"**Interpretation and method**: {p['note']}"]
    try:
        import graeca as G
        body = G.text(p["work"], p["locus"])
        w = G.work(p["work"])
        out += ["", f"<details><summary>Greek ({w['author']}, {w['title']})</summary>\n\n> " + body[:4000] + ("…" if len(body) > 4000 else "") + "\n</details>"]
    except Exception:
        pass
    out += ["", "### Checks (recomputed now)"]
    out += [f"* {'✅' if ch.ok else '❌'} `{ch.method}` {label}" for label, ch in M.run(pid)]
    return "\n".join(out)


def works():
    import graeca as G
    out = ["## Greek mathematical texts beyond the Elements", "",
           "`tei`: curated encoding (First1KGreek). `ocr`: machine transcription by printed page (Open Greek Corpus); "
           "unresolved readings stay as ⟦a ∥ b⟧ and must be collated before citing.", "",
           "| work | author | title | transmission | passages |", "|---|---|---|---|---|"]
    out += [f"| `{w['id']}` | {w['author']} | {w['title']} | {w['transmission']} | {w['passages']} |" for w in G.INDEX]
    out.append("\nRead one with `text <work> <locus>`; list loci with `text <work>`.")
    return "\n".join(out)


def greek_text(arg):
    import graeca as G
    wid, _, locus = arg.strip().partition(" ")
    try:
        w = G.work(wid)
    except KeyError:
        near = [x["id"] for x in G.INDEX if wid and wid.lower() in x["id"]]
        return f"No work `{wid}`." + (f" Did you mean {', '.join(f'`{k}`' for k in near)}?" if near else " Try `works`.")
    if not locus.strip():
        return f"## {w['author']}, {w['title']}\n\nLoci ({w['units']}): " + ", ".join(f"`{l}`" for l in G.loci(wid))
    try:
        body = G.text(wid, locus.strip())
    except KeyError:
        return f"`{wid}` has no locus `{locus.strip()}`. Loci: " + ", ".join(f"`{l}`" for l in G.loci(wid)[:80])
    head = [f"## {w['author']}, {w['title']}, {locus.strip()}", f"*{w['edition'][:300]}*",
            f"Source: [{w['source']['repo']} `{w['source']['path']}`]({w['source']['url']}), {w['licence']}"]
    if w["transmission"] == "ocr":
        head.append(f"> **Caution**: {w.get('caution', 'machine OCR')}")
    return "\n\n".join(head + ["> " + body])


def greek_search(pattern):
    import graeca as G
    if not pattern.strip():
        return "Give Greek text to search for, for example `greek μέναιχμ`."
    hits = G.search(pattern)
    rows = [f"| `{w}` | `{l}` |" for w, l in hits[:150]]
    more = f"\n\n…and {len(hits) - 150} more." if len(hits) > 150 else ""
    return f"## “{pattern}” in the Greek texts: {len(hits)} passages\n\n| work | locus |\n|---|---|\n" + "\n".join(rows) + more


def normalise(rid):
    rid = rid.strip().strip("`")
    m = re.fullmatch(r"(?i)([ivxl]+)[.\s]*(.*)", rid)
    return (m.group(1).upper() + ("." + m.group(2) if m.group(2) else "")) if m else rid


def ask(text):
    """Accept `verify`, `list`, `part <id>`, `prop <id>`, `search <text>`, or a bare id."""
    text = text.strip()
    cmd, _, arg = text.partition(" ")
    cmd = cmd.lower().lstrip("/")
    if cmd in ("verify", "list"):
        return verify()[0] if cmd == "verify" else listing()
    if cmd == "part":
        return part(arg.strip())
    if cmd in ("prop", "proposition", "elements"):
        return prop(arg)
    if cmd == "search":
        return search(arg.strip())
    if cmd == "works":
        return works()
    if cmd == "archimedes":
        return archimedes_list()
    if cmd == "auctores":
        return auctores_list()
    if cmd == "arch":
        return archimedes_prop(arg)
    if cmd == "text":
        return greek_text(arg)
    if cmd == "greek":
        return greek_search(arg)
    if text in BYID:
        return part(text)
    if re.fullmatch(r"(?i)[ivxl]+\.[\w.]+", text):
        return prop(text)
    return search(text)


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd, arg = argv[1], " ".join(argv[2:])
    if cmd == "verify":
        text, bad = verify()
        parts, bads = [text], [bad]
        for name, title in SUITES:
            tx, bd = verify_suite(name, title)
            parts.append(tx)
            bads.append(bd)
        print("\n\n".join(parts))
        sys.exit(1 if any(bads) else 0)
    text = {"list": lambda: listing(), "part": lambda: part(arg), "prop": lambda: prop(arg),
            "search": lambda: search(arg), "ask": lambda: ask(arg), "works": lambda: works(),
            "text": lambda: greek_text(arg), "greek": lambda: greek_search(arg),
            "archimedes": lambda: archimedes_list(), "auctores": lambda: auctores_list(),
            "arch": lambda: archimedes_prop(arg)}.get(cmd, lambda: __doc__)()
    if len(text) > LIMIT:
        text = text[:LIMIT] + "\n\n*(truncated; run locally for the full output)*"
    print(text)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main(sys.argv)
