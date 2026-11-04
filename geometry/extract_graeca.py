"""Greek mathematical texts beyond the Elements, extracted from two GitHub corpora into graeca/*.json.

    python extract_graeca.py FIRST1K_DIR OGC_DIR

FIRST1K_DIR  a checkout of OpenGreekAndLatin/First1KGreek (TEI, curated)
OGC_DIR      a checkout of open-greek/open-greek-corpus (JSON Lines; used only for books that First1KGreek lacks,
             all of them machine OCR of the printed edition)

Each work becomes a record with its edition, its source file at a pinned commit, its licence and its transmission:
"tei" for a curated encoding, "ocr" for a machine transcription that still has to be collated with the printed page.
Passages keep the citation units of the encoding (book.proposition for most works). Editorial deletions <del> are kept
in square brackets; figures are counted, not reproduced. Unresolved OCR readings stay in the form ⟦a ∥ b⟧.
"""
import json
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

TEI = "{http://www.tei-c.org/ns/1.0}"
OUT = pathlib.Path(__file__).parent / "graeca"

# (group file, author, work id, TEI path under data/, title, unit note, book offset)
FIRST1K = [
    ("archimedes", "Archimedes", "sphaera-cylindrus", "tlg0552/tlg001/tlg0552.tlg001.1st1K-grc1.xml", "De sphaera et cylindro", "book.proposition (pr = preface)", 0),
    ("archimedes", "Archimedes", "dimensio-circuli", "tlg0552/tlg002/tlg0552.tlg002.1st1K-grc1.xml", "Dimensio circuli", "proposition", 0),
    ("archimedes", "Archimedes", "conoides", "tlg0552/tlg003/tlg0552.tlg003.1st1K-grc1.xml", "De conoidibus et sphaeroidibus", "proposition (pr = preface)", 0),
    ("archimedes", "Archimedes", "spirales", "tlg0552/tlg004/tlg0552.tlg004.1st1K-grc1.xml", "De lineis spiralibus", "proposition (pr = preface)", 0),
    ("archimedes", "Archimedes", "aequilibria", "tlg0552/tlg005/tlg0552.tlg005.1st1K-grc1.xml", "De planorum aequilibriis", "book.proposition", 0),
    ("archimedes", "Archimedes", "arenarius", "tlg0552/tlg006/tlg0552.tlg006.1st1K-grc1.xml", "Arenarius", "chapter", 0),
    ("archimedes", "Archimedes", "quadratura-parabolae", "tlg0552/tlg007/tlg0552.tlg007.1st1K-grc1.xml", "Quadratura parabolae", "proposition (pr = preface)", 0),
    ("archimedes", "Archimedes", "fluitantia", "tlg0552/tlg008/tlg0552.tlg008.1st1K-grc1.xml", "De corporibus fluitantibus", "book.proposition", 0),
    ("archimedes", "Archimedes", "stomachion", "tlg0552/tlg009/tlg0552.tlg009.1st1K-grc1.xml", "Stomachion", "fragment", 0),
    ("archimedes", "Archimedes", "methodus", "tlg0552/tlg010/tlg0552.tlg010.1st1K-grc1.xml", "Ad Eratosthenem methodus", "proposition (pr = preface)", 0),
    ("archimedes", "Archimedes", "liber-assumptorum", "tlg0552/tlg011/tlg0552.tlg011.1st1K-grc1.xml", "Liber assumptorum (Greek)", "proposition", 0),
    ("archimedes", "Archimedes", "liber-assumptorum-lat", "tlg0552/tlg011/tlg0552.tlg011.1st1K-lat1.xml", "Liber assumptorum (Latin, from the Arabic)", "proposition", 0),
    ("archimedes", "Archimedes", "problema-bovinum", "tlg0552/tlg012/tlg0552.tlg012.1st1K-grc1.xml", "Problema bovinum", "chapter", 0),
    ("archimedes", "Archimedes", "fragmenta", "tlg0552/tlg013/tlg0552.tlg013.1st1K-grc1.xml", "Fragmenta", "fragment", 0),
    ("eutocius", "Eutocius", "in-sphaeram-cylindrum", "tlg4072/tlg001/tlg4072.tlg001.1st1K-grc1.xml", "Commentarii in libros De sphaera et cylindro", "section", 0),
    ("eutocius", "Eutocius", "in-dimensionem-circuli", "tlg4072/tlg002/tlg4072.tlg002.1st1K-grc1.xml", "Commentarius in Dimensionem circuli", "section.paragraph", 0),
    ("eutocius", "Eutocius", "in-aequilibria", "tlg4072/tlg003/tlg4072.tlg003.1st1K-grc1.xml", "Commentarius in libros De planorum aequilibriis", "chapter.section", 0),
    ("apollonius", "Apollonius Pergaeus", "conica-4", "tlg0550/tlg001/tlg0550.tlg001.1st1K-grc1.xml", "Conica, Book IV", "proposition (locus prefixed with book 4)", None),
    ("pappus", "Pappus Alexandrinus", "synagoge-2-5", "tlg2032/tlg001/tlg2032.tlg001.1st1K-grc1.xml", "Synagoge (Collectio), Books II to V", "book.chapter (the encoding numbers Hultsch's Books II to V as 1 to 4; corrected here)", 1),
    ("euclid-minora", "Euclides", "data", "tlg1799/tlg007/tlg1799.tlg007.1st1K-grc1.xml", "Data", "section (definitions, then propositions)", 0),
    ("euclid-minora", "Euclides", "data-alterae", "tlg1799/tlg008/tlg1799.tlg008.1st1K-grc1.xml", "Data, demonstrationes alterae", "section", 0),
    ("euclid-minora", "Euclides", "optica", "tlg1799/tlg009/tlg1799.tlg009.1st1K-grc1.xml", "Optica", "proposition", 0),
    ("euclid-minora", "Euclides", "optica-theonis", "tlg1799/tlg010/tlg1799.tlg010.1st1K-grc1.xml", "Opticorum recensio Theonis", "proposition", 0),
    ("euclid-minora", "Euclides", "catoptrica", "tlg1799/tlg011/tlg1799.tlg011.1st1K-grc1.xml", "Catoptrica (recensio Theonis?)", "proposition", 0),
    ("euclid-minora", "Euclides", "phaenomena", "tlg1799/tlg012/tlg1799.tlg012.1st1K-grc1.xml", "Phaenomena", "proposition", 0),
    ("euclid-minora", "Euclides", "phaenomena-b", "tlg1799/tlg013/tlg1799.tlg013.1st1K-grc1.xml", "Phaenomena (recensio b)", "work", 0),
    ("euclid-minora", "Euclides", "phaenomena-b-alterae", "tlg1799/tlg014/tlg1799.tlg014.1st1K-grc1.xml", "Phaenomena (demonstrationes alterae recensionis b)", "chapter", 0),
    ("euclid-minora", "Euclides", "sectio-canonis", "tlg1799/tlg015/tlg1799.tlg015.1st1K-grc1.xml", "Sectio canonis [Sp.]", "chapter", 0),
    ("euclid-minora", "Euclides", "fragmenta", "tlg1799/tlg016/tlg1799.tlg016.1st1K-grc1.xml", "Fragmenta", "chapter.section", 0),
    ("euclid-minora", "Marinus", "marinus-in-data", "tlg4075/tlg002/tlg4075.tlg002.1st1K-grc1.xml", "Commentarium in Euclidis Data", "work", 0),
    ("sphaerica", "Theodosius", "theodosius-sphaerica", "tlg1719/tlg001/tlg1719.tlg001.1st1K-grc1.xml", "Sphaerica", "book.proposition.section", 0),
    ("sphaerica", "Autolycus", "autolycus-sphaera", "tlg1210/tlg001/tlg1210.tlg001.1st1K-grc1.xml", "De sphaera quae movetur", "chapter.section", 0),
    ("sphaerica", "Autolycus", "autolycus-ortus", "tlg1210/tlg002/tlg1210.tlg002.1st1K-grc1.xml", "De ortibus et occasibus", "book.chapter.section", 0),
    ("sphaerica", "Aristarchus", "aristarchus-magnitudines", "tlg1181/tlg001/tlg1181.tlg001.1st1K-grc1.xml", "De magnitudinibus et distantiis solis et lunae", "proposition", 0),
    ("sphaerica", "Geminus", "geminus-elementa", "tlg1383/tlg001/tlg1383.tlg001.1st1K-grc1.xml", "Elementa astronomiae", "chapter", 0),
    ("ptolemy", "Claudius Ptolemaeus", "syntaxis", "tlg0363/tlg001/tlg0363.tlg001.1st1K-grc1.xml", "Syntaxis mathematica (Almagest)", "book.chapter", 0),
    ("hero", "Hero Alexandrinus", "metrica", "tlg0559/tlg006/tlg0559.tlg006.1st1K-grc1.xml", "Metrica", "book.chapter", 0),
    ("hero", "Hero Alexandrinus", "dioptra", "tlg0559/tlg007/tlg0559.tlg007.1st1K-grc1.xml", "Dioptra", "chapter", 0),
    ("hero", "Hero Alexandrinus", "catoptrica", "tlg0559/tlg005/tlg0559.tlg005.1st1K-grc1.xml", "Catoptrica (fragment)", "chapter", 0),
    ("hero", "Hero Alexandrinus", "stereometrica", "tlg0559/tlg010/tlg0559.tlg010.1st1K-grc1.xml", "Stereometrica", "book.chapter.section", 0),
    ("hero", "Hero Alexandrinus", "de-mensuris", "tlg0559/tlg011/tlg0559.tlg011.1st1K-grc1.xml", "De mensuris", "chapter.section", 0),
    ("hero", "Hero Alexandrinus", "geodaesia", "tlg0559/tlg015/tlg0559.tlg015.1st1K-grc1.xml", "Geodaesia [Sp.]", "chapter.section", 0),
    ("hero", "Hero Alexandrinus", "geeponicus", "tlg0559/tlg016/tlg0559.tlg016.1st1K-grc1.xml", "Liber geeponicus [Sp.]", "chapter", 0),
    ("arithmetica", "Nicomachus Gerasenus", "nicomachus-introductio", "tlg0358/tlg001/tlg0358.tlg001.1st1K-grc1.xml", "Introductio arithmetica", "book.chapter", 0),
    ("arithmetica", "Theon Smyrnaeus", "theon-utilitas", "tlg1724/tlg001/tlg1724.tlg001.1st1K-grc1.xml", "De utilitate mathematicae", "chapter", 0),
]

# Books absent from First1KGreek, taken from the OCR layer of the Open Greek Corpus.
OGC = [
    ("apollonius", "Apollonius Pergaeus", "conica-1-3", "data/corpus_extensions/apollonius-geom.conica.jsonl", "Conica, Books I to III",
     "book.page of Heiberg's edition (OCR consensus by printed page, not by proposition)", lambda r: r["locus"].split(".")[0] in ("1", "2", "3")),
    ("pappus", "Pappus Alexandrinus", "synagoge-6-8", "data/corpus_extensions/pappus-mathematics.synagoge.jsonl", "Synagoge (Collectio), Books VI to VIII",
     "book.page of Hultsch's edition (OCR consensus by printed page)", lambda r: True),
]


def commit(repo):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def text_of(el):
    """Running text of an element: <del> in brackets, notes and figures dropped, line breaks as spaces."""
    out = []

    def walk(e):
        tag = e.tag.replace(TEI, "")
        if tag in ("note", "figure", "graphic", "bibl"):
            out.append(e.tail or "")
            return
        if tag == "lb":
            out.append("" if e.get("break") == "no" else " ")
        if tag == "del":
            out.append("[")
        out.append(e.text or "")
        for c in e:
            if c.tag.replace(TEI, "") == "div" and c.get("type") == "textpart":
                continue
            walk(c)
        if tag == "del":
            out.append("]")
        out.append(e.tail or "")

    walk(el)
    return re.sub(r"\s+", " ", "".join(out[:-1] if out else out)).strip()


def passages(path, offset):
    root = ET.parse(path).getroot()
    edition = root.find(f".//{TEI}div[@type='edition']")
    if edition is None:
        edition = root.find(f".//{TEI}div[@type='translation']")
    res = []

    def walk(div, locus):
        kids = [c for c in div if c.tag == f"{TEI}div" and c.get("type") == "textpart"]
        own = text_of(div)
        if kids and own:
            res.append({"locus": ".".join(locus + ["pre"]) if locus else "pre", "text": own, "figures": 0})
        if not kids and locus:
            res.append({"locus": ".".join(locus), "text": own, "figures": len(div.findall(f".//{TEI}figure"))})
        for c in kids:
            walk(c, locus + [c.get("n", "?")])

    walk(edition, [])
    if offset:
        for p in res:
            head, _, rest = p["locus"].partition(".")
            if head.isdigit():
                p["locus"] = str(int(head) + offset) + ("." + rest if rest else "")
    if offset is None:  # Conica IV: the encoding numbers propositions only
        for p in res:
            p["locus"] = "4." + p["locus"]
    return [p for p in res if p["text"]]


def edition_of(path):
    t = path.read_text()
    m = re.search(r"<sourceDesc>(.*?)</sourceDesc>", t, re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip() if m else ""


def main(first1k, ogc):
    first1k, ogc = pathlib.Path(first1k), pathlib.Path(ogc)
    c1, c2 = commit(first1k), commit(ogc)
    groups = {}
    for group, author, wid, rel, title, unit, offset in FIRST1K:
        path = first1k / "data" / rel
        ps = passages(path, offset)
        groups.setdefault(group, []).append(dict(
            id=f"{group}.{wid}", author=author, title=title, units=unit, transmission="tei",
            edition=edition_of(path), licence="CC BY-SA 4.0",
            source=dict(repo="OpenGreekAndLatin/First1KGreek", commit=c1, path=f"data/{rel}",
                        url=f"https://github.com/OpenGreekAndLatin/First1KGreek/blob/{c1}/data/{rel}"),
            passages=ps))
    for group, author, wid, rel, title, unit, keep in OGC:
        rows = [json.loads(l) for l in (ogc / rel).open()]
        rows = [r for r in rows if keep(r)]
        ps = [{"locus": r["locus"], "text": r["text"], "page": r.get("printed_page")} for r in rows]
        groups.setdefault(group, []).append(dict(
            id=f"{group}.{wid}", author=author, title=title, units=unit, transmission="ocr",
            edition=str(rows[0].get("edition")), licence=str(rows[0].get("license")),
            caution="Machine OCR of the printed edition with unresolved readings marked ⟦a ∥ b⟧. Collate with the page before citing.",
            source=dict(repo="open-greek/open-greek-corpus", commit=c2, path=rel,
                        url=f"https://github.com/open-greek/open-greek-corpus/blob/{c2}/{rel}"),
            passages=ps))
    OUT.mkdir(exist_ok=True)
    index = []
    for group, works in groups.items():
        (OUT / f"{group}.json").write_text(json.dumps(works, ensure_ascii=False, indent=0))
        for w in works:
            index.append(dict(id=w["id"], author=w["author"], title=w["title"], transmission=w["transmission"],
                              passages=len(w["passages"]), units=w["units"], file=f"graeca/{group}.json"))
            print(f"{w['id']:40s} {w['transmission']:4s} {len(w['passages']):5d}  {w['title']}")
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
