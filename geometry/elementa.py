"""The complete Elements as data: every definition, postulate, common notion and proposition of Books I to XIII.

Reads elements.json (written by extract_elements.py). Ids follow book and number: "I.47", "XIII.18",
"I.def.15", "I.post.5", "I.cn.1" (Heiberg's numbering), "X.def.2.3" (Book X, second group of definitions).

    import elementa as E
    E.get("I.47")["enunciation"]          # Heath 1908
    E.get("I.47")["greek"]                # Heiberg 1883-1888
    E.cites("I.47")                       # Heath's bracketed references, in order of appearance
    E.foundations("I.47")                 # every record I.47 rests on, transitively
    E.uses_parallel_postulate("I.47")     # True
    E.geocoq("I.47")                      # Coq source of each GeoCoq file for the proposition
    E.lean("I.47")                        # Lean 4 source of the LeanEuclid file
    E.search("extreme and mean ratio")

The citation graph is Heath's editorial apparatus, not Euclid's text, which cites nothing. Treat every
result derived from it as interpretation.

    python elementa.py                    # summary of the whole graph
"""
import json
import pathlib
import re
from functools import lru_cache

ROOT = pathlib.Path(__file__).parent
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]


def _load():
    """Read elements.json in either layout: the full one written by extract_elements.py (records keyed by id)
    or the compact one embedded in site.html (a list of records with short keys)."""
    d = json.loads((ROOT / "elements.json").read_text())
    if isinstance(d["records"], list):
        d["records"] = {r["id"]: dict(
            id=r["id"], book=ROMAN[int(r["b"]) - 1], kind=r["k"], number=r["n"], page=r.get("page"),
            enunciation=r.get("en") or "", proof=r.get("pr") or "", greek=r.get("gr") or "",
            notes=r.get("notes") or [], cites=r.get("c") or [], cited_by=r.get("cb") or [],
            geocoq=r.get("gc") or [], lean=r.get("ln")) for r in d["records"]}
        d["geocoq"] = {k: dict(file=v["file"], source=v["src"], requires=v.get("req", [])) for k, v in d["geocoq"].items()}
        d["lean"] = {k: dict(file=v["file"], source=v["src"], uses=v.get("uses", [])) for k, v in d["lean"].items()}
    return d


_D = _load()
RECORDS = _D["records"]
SOURCES = _D["sources"]
GAPS = _D["gaps"]


def get(rid):
    return RECORDS[rid]


def ids(book=None, kind=None):
    return [k for k, r in RECORDS.items() if (book is None or r["book"] == book) and (kind is None or r["kind"] == kind)]


def cites(rid):
    return list(RECORDS[rid]["cites"])


def cited_by(rid):
    return list(RECORDS[rid]["cited_by"])


@lru_cache(maxsize=None)
def _closure(rid):
    seen = set()
    stack = list(RECORDS[rid]["cites"])
    while stack:
        c = stack.pop()
        if c in seen or c == rid:
            continue
        seen.add(c)
        stack.extend(RECORDS[c]["cites"])
    return frozenset(seen)


def foundations(rid, kind=None):
    """Every record rid depends on through Heath's citations, sorted in the order of the Elements."""
    order = {k: i for i, k in enumerate(RECORDS)}
    return sorted((c for c in _closure(rid) if kind is None or RECORDS[c]["kind"] == kind), key=order.get)


def uses_parallel_postulate(rid):
    return rid == "I.post.5" or "I.post.5" in _closure(rid)


def geocoq(rid):
    """{file stem: Coq source} for each GeoCoq file proving the proposition (Book I only)."""
    return {s: _D["geocoq"][s]["source"] for s in RECORDS[rid].get("geocoq", [])}


def geocoq_requires(stem, transitive=False):
    req = _D["geocoq"][stem]["requires"]
    if not transitive:
        return list(req)
    seen, stack = [], list(req)
    while stack:
        s = stack.pop(0)
        if s in seen or s not in _D["geocoq"]:
            continue
        seen.append(s)
        stack.extend(_D["geocoq"][s]["requires"])
    return seen


def lean(rid):
    n = RECORDS[rid].get("lean")
    return _D["lean"][str(n)]["source"] if n else None


def search(text):
    t = text.lower()
    return [k for k, r in RECORDS.items() if t in (r["enunciation"] + " " + r["proof"]).lower()]


def summary():
    props = ids(kind="prop")
    pp = [k for k in props if uses_parallel_postulate(k)]
    deep = max(props, key=lambda k: len(_closure(k)))
    return dict(records=len(RECORDS), propositions=len(props),
                citations=sum(len(r["cites"]) for r in RECORDS.values()),
                parallel_postulate=len(pp), first_using_parallel=pp[0] if pp else None,
                deepest=deep, deepest_foundations=len(_closure(deep)),
                most_cited=max(RECORDS, key=lambda k: len(RECORDS[k]["cited_by"])),
                uncited_propositions=sum(1 for k in props if not RECORDS[k]["cited_by"]),
                greek_missing=GAPS["missing_greek"])


if __name__ == "__main__" and len(__import__("sys").argv) > 1:
    import sys
    cmd, arg = sys.argv[1], " ".join(sys.argv[2:])
    if cmd == "get":
        r = get(arg)
        print(f"{arg}\n\n{r['enunciation']}\n\n{r['greek']}\n\ncites: {', '.join(r['cites']) or 'nothing'}")
        print(f"cited by: {', '.join(r['cited_by']) or 'nothing'}\nrests on Post. 5: {uses_parallel_postulate(arg)}")
    elif cmd == "search":
        print("\n".join(search(arg)))
    elif cmd == "foundations":
        print("\n".join(foundations(arg)))
    else:
        sys.exit("usage: python elementa.py [get ID | search TEXT | foundations ID]")
elif __name__ == "__main__":
    for k, v in summary().items():
        print(f"{k:24s} {v}")
    print("I.47 rests on", len(foundations("I.47")), "records, postulates:", foundations("I.47", "post"))
    print("GeoCoq proposition_47 needs", len(geocoq_requires("proposition_47", transitive=True)), "files")
