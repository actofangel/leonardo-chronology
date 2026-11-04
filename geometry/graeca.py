"""Greek mathematical texts beyond the Elements (graeca/*.json, written by extract_graeca.py).

    import graeca as G
    G.works()                                          # every work: id, author, title, transmission, passages
    G.text("archimedes.sphaera-cylindrus", "1.33")     # one passage
    G.search("μέναιχμ")                                 # accent and case insensitive; returns (work, locus)
    G.sources("apollonius-circle")                     # Greek passages behind a corpus part

Transmission "tei" is a curated encoding; "ocr" is a machine transcription with unresolved readings ⟦a ∥ b⟧
and page level loci, to be collated with the printed edition before citing.

    python graeca.py                                   # list the works
    python graeca.py text archimedes.dimensio-circuli 3
    python graeca.py search ἕλιξ
"""
import json
import pathlib
import re
import sys
import unicodedata
from functools import lru_cache

ROOT = pathlib.Path(__file__).parent
INDEX = json.loads((ROOT / "graeca" / "index.json").read_text())
LINKS = json.loads((ROOT / "graeca" / "links.json").read_text())


def norm(s):
    s = unicodedata.normalize("NFD", s.lower().replace("ς", "σ"))
    return "".join(c for c in s if not unicodedata.combining(c))


@lru_cache(maxsize=None)
def _file(path):
    return {w["id"]: w for w in json.loads((ROOT / path).read_text())}


def work(wid):
    entry = next((w for w in INDEX if w["id"] == wid), None)
    if not entry:
        raise KeyError(f"no work {wid}")
    return _file(entry["file"])[wid]


def works(author=None):
    return [w for w in INDEX if author is None or norm(author) in norm(w["author"])]


def loci(wid):
    return [p["locus"] for p in work(wid)["passages"]]


def text(wid, locus):
    for p in work(wid)["passages"]:
        if p["locus"] == str(locus):
            return p["text"]
    raise KeyError(f"{wid} has no locus {locus}")


def search(pattern, wid=None):
    rx = re.compile(norm(pattern))
    hits = []
    for w in INDEX:
        if wid and w["id"] != wid:
            continue
        for p in work(w["id"])["passages"]:
            if rx.search(norm(p["text"])):
                hits.append((w["id"], p["locus"]))
    return hits


def sources(part_id):
    """[(work, locus, note)] for a corpus part, from graeca/links.json."""
    return [(l["work"], l["locus"], l.get("note", "")) for l in LINKS.get(part_id, [])]


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        for w in INDEX:
            print(f"{w['id']:40s} {w['transmission']:4s} {w['passages']:5d}  {w['author']}, {w['title']}")
    elif a[0] == "text":
        print(text(a[1], a[2]))
    elif a[0] == "search":
        for h in search(" ".join(a[1:])):
            print(*h)
    else:
        sys.exit(__doc__)
