"""Build elements.json: the complete Elements (13 books) with every formalisation held locally.

Sources, all copied into vendor/ at pinned commits:
  vendor/perseus     Heiberg's Greek (Teubner 1883-1888) and Heath's English (Cambridge 1908), Perseus TEI,
                     CC BY-SA 4.0, PerseusDL/canonical-greekLit data/tlg1799/tlg001
  vendor/geocoq      GeoCoq theories/Elements/OriginalProofs (Coq/Rocq), LGPL-3.0
  vendor/leaneuclid  LeanEuclid Book/PropNN.lean (Lean 4, System E), MIT

Every definition, postulate, common notion and proposition gets one record. Heath's bracketed citations
([I. 4], [Post. 2], ...) are TEI <ref> elements, so the dependency graph of the whole Elements is read
from the markup, not guessed. GeoCoq dependencies come from its Require lines, Lean ones from the
proposition_N names its proofs apply.

    python extract_elements.py
"""
import json
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parent
V = ROOT / "vendor"
T = "{http://www.tei-c.org/ns/1.0}"
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]
KIND = {"def": "def", "post": "post", "comm_not": "cn", "prop": "prop"}


def kind_of(section):
    return KIND[re.sub(r"_?\d$", "", section)]


def ident(book, kind, n, section=""):
    """Book X has three groups of definitions (def_1 .. def_3); they are numbered X.def.G.N."""
    if kind == "prop":
        return f"{ROMAN[book]}.{n}"
    group = re.search(r"(\d)$", section)
    return f"{ROMAN[book]}.{kind}.{group.group(1)}.{n}" if group else f"{ROMAN[book]}.{kind}.{n}"


def norm_ref(target):
    """elem.1.4 -> I.4, elem.1.post.2 -> I.post.2, elem.1.c.n.1 -> I.cn.1, elem.10.def.2.3 -> X.def.2.3"""
    p = target.split(".")[1:]
    if not p or not p[0].isdigit() or not 1 <= int(p[0]) <= 13:
        return None
    b = ROMAN[int(p[0])]
    rest = p[1:]
    if rest[:2] == ["c", "n"]:
        return f"{b}.cn.{rest[2]}" if len(rest) > 2 else None
    if rest and rest[0] in ("def", "post"):
        return f"{b}.{'.'.join(rest)}"
    if rest and rest[0].isdigit():
        return f"{b}.{rest[0]}"
    return None


def text_of(e, refs, skip=("note", "figure", "label", "head")):
    """Plain text of a TEI element. <emph> letters stay plain, <del> (Heiberg's athetesis) becomes [[ ]]."""
    out = []

    def go(x):
        tag = x.tag.replace(T, "")
        if tag in skip:
            out.append(x.tail or "")
            return
        if tag == "ref" and refs is not None:
            for t in (x.get("target") or "").split():
                r = norm_ref(t)
                if r:
                    refs.append(r)
        if tag == "del":
            out.append("[[")
        out.append(x.text or "")
        for k in x:
            go(k)
        if tag == "del":
            out.append("]]")
        if tag == "p":
            out.append("\n\n")
        out.append(x.tail or "")

    go(e)
    return re.sub(r"[ \t\r\n]*\n\n[ \t\r\n]*", "\n\n", re.sub(r"[ \t]*\n[ \t]*(?!\n)", " ",
                  re.sub(r"[ \t]+", " ", "".join(out)))).strip()


def walk_sections(path):
    body = ET.parse(path).getroot().find(f".//{T}body")
    for book in body.iter(T + "div"):
        if book.get("subtype") != "book":
            continue
        b = int(book.get("n"))
        for sec in book:
            if sec.get("subtype") != "type":
                continue
            for num in sec:
                if num.get("subtype") == "number":
                    yield b, sec.get("n"), num


def heath():
    out = {}
    page = None
    for b, sec, num in walk_sections(V / "perseus/tlg1799.tlg001.perseus-eng2.xml"):
        k = kind_of(sec)
        pbs = [p.get("n") for p in num.iter(T + "pb")]
        start = page
        page = pbs[-1] if pbs else page
        refs = []
        paras = [p for p in num if p.tag == T + "p"]
        enun, proof = "", []
        for p in paras:
            lab = p.find(T + "label")
            t = text_of(p, refs)
            if lab is not None and (lab.text or "").startswith("Enunciation"):
                enun = t
            else:
                proof.append(t)
        if not enun and paras and k == "prop":
            enun, proof = proof[0], proof[1:]
        rec = dict(id=ident(b, k, num.get("n"), sec), book=b, kind=k, n=num.get("n"), section=sec,
                   heath_page=_page_at_start(num, start))
        first_text = text_of(num, None, skip=("note", "figure", "head"))
        rec["enunciation"] = enun if k == "prop" else "\n\n".join(proof) or first_text
        rec["proof"] = "\n\n".join(proof) if k == "prop" else ""
        rec["notes"] = [text_of(n, None, skip=("figure",)) for n in num.iter(T + "note")]
        rec["figures"] = sum(1 for _ in num.iter(T + "figure"))
        seen = []
        for r in refs:
            if r not in seen and r != rec["id"]:
                seen.append(r)
        rec["cites"] = seen
        out[rec["id"]] = rec
    return out


def _page_at_start(num, previous):
    """Heath page where the record begins: a <pb> before any text, else the page still running."""
    for x in num.iter():
        if x.tag == T + "pb":
            return x.get("n")
        if x.tag == T + "p" and (x.text or "").strip():
            return previous
    return previous


def heiberg():
    out = {}
    for b, sec, num in walk_sections(V / "perseus/tlg1799.tlg001.perseus-grc2.xml"):
        k = kind_of(sec)
        out[ident(b, k, num.get("n"), sec)] = text_of(num, None, skip=("note", "figure", "head"))
    return out


def git_head(repo):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def geocoq():
    d = V / "geocoq/theories/Elements/OriginalProofs"
    files = {}
    for f in sorted(d.glob("*.v")):
        src = f.read_text()
        req = re.findall(r"Require (?:Export|Import) GeoCoq\.Elements\.OriginalProofs\.(\w+)\.", src)
        names = re.findall(r"^(?:Lemma|Theorem|Proposition) (\w+)", src, re.M)
        files[f.stem] = dict(file=f"theories/Elements/OriginalProofs/{f.name}", requires=req, declares=names,
                             lines=src.count("\n"), source=src)
    return files


def lean():
    d = V / "leaneuclid/Book"
    out = {}
    for f in sorted(d.glob("Prop*.lean")):
        src = f.read_text()
        n = int(f.stem[4:])
        uses = sorted({int(m) for m in re.findall(r"\bproposition_(\d+)", src)} - {n})
        out[n] = dict(file=f"Book/{f.name}", uses=uses, lines=src.count("\n"), source=src)
    return out


def main():
    rec = heath()
    grc = heiberg()
    missing_greek = []
    for k, r in rec.items():
        r["greek"] = grc.get(k)
        if r["greek"] is None:
            missing_greek.append(k)
    greek_only = sorted(set(grc) - set(rec))
    gc, ln = geocoq(), lean()
    for k, r in rec.items():
        if r["book"] == 1 and r["kind"] == "prop":
            n = int(r["n"])
            stems = sorted(s for s in gc if re.fullmatch(rf"proposition_{n:02d}[A-Z]?", s))
            r["geocoq"] = stems
            r["lean"] = n if n in ln else None
    # Heath cites Book X's first definitions as "X. Def. N", and numbers the common notions 1 to 5 where the
    # Perseus encoding keeps Heiberg's numbers (Heath's C.N. 4 and 5 are Heiberg's 7 and 8).
    alias = {"I.cn.4": "I.cn.7", "I.cn.5": "I.cn.8"}
    for r in rec.values():
        fixed = []
        for c in r["cites"]:
            c = alias.get(c, c)
            if c not in rec and re.fullmatch(r"X\.def\.\d+", c):
                c = "X.def.1." + c.split(".")[-1]
            if c not in fixed:
                fixed.append(c)
        r["cites"] = fixed
    # cited_by, the inverse graph
    for r in rec.values():
        r["cited_by"] = []
    for r in rec.values():
        for c in r["cites"]:
            if c in rec:
                rec[c]["cited_by"].append(r["id"])
    sources = {
        "heath": dict(name="Heath, The Thirteen Books of Euclid's Elements, Cambridge 1908 (Perseus TEI perseus-eng2)",
                      license="CC BY-SA 4.0 (Perseus encoding); Heath's 1908 text is in the public domain",
                      repo="PerseusDL/canonical-greekLit", path="data/tlg1799/tlg001/tlg1799.tlg001.perseus-eng2.xml"),
        "heiberg": dict(name="Heiberg, Euclidis Elementa, Leipzig: Teubner 1883-1888 (Perseus TEI perseus-grc2)",
                        license="CC BY-SA 4.0 (Perseus encoding); Heiberg's text is in the public domain",
                        repo="PerseusDL/canonical-greekLit", path="data/tlg1799/tlg001/tlg1799.tlg001.perseus-grc2.xml"),
        "geocoq": dict(name="GeoCoq, Elements/OriginalProofs (Beeson, Narboux, Wiedijk)", license="LGPL-3.0",
                       repo="GeoCoq/GeoCoq", commit=git_head(V / "geocoq")),
        "leaneuclid": dict(name="LeanEuclid, Book I in System E (Murphy et al.)", license="MIT",
                           repo="loganrjmurphy/LeanEuclid", commit=git_head(V / "leaneuclid")),
    }
    perseus_commit = (V / "perseus/COMMIT").read_text().strip() if (V / "perseus/COMMIT").exists() else None
    sources["heath"]["commit"] = sources["heiberg"]["commit"] = perseus_commit
    out = dict(sources=sources, records=rec, geocoq=gc, lean=ln,
               gaps=dict(missing_greek=missing_greek, greek_only=greek_only))
    (ROOT / "elements.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
    kinds = {}
    for r in rec.values():
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("records", len(rec), kinds)
    print("citations", sum(len(r["cites"]) for r in rec.values()))
    print("unresolved", sorted({c for r in rec.values() for c in r["cites"] if c not in rec}))
    print("greek missing", missing_greek, "greek only", greek_only)
    print("geocoq files", len(gc), "lean props", len(ln))


if __name__ == "__main__":
    main()
