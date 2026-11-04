# Corpus Geometriae

Classical geometry as code: constructions and propositions from Hippocrates of Chios, Euclid, Archimedes, Apollonius and Ptolemy to Alberti, Pacioli and Leonardo, each a self contained part with its locus in the source, separated factual, interpretive and hypothesis layers, a GeoGebra command sequence, a Python construction and a sympy verification. Alongside it, the complete Elements (Heiberg's Greek, Heath's English) with Heath's citation graph and the machine checked formalisations of Book I.

This folder sits beside the database and is not read by `scripts/validate.mjs` or `scripts/build.mjs`.

## Contents

| Path | Contents |
| --- | --- |
| `geometria.py` | All 22 parts as Python functions; running it executes every verification |
| `parts.json` | Machine readable part records (traditions, layers, checks, GeoGebra, figures, Newclid results) |
| `elementa.py` | Library over `elements.json`: lookup, search, citation graph, foundations, parallel postulate dependence |
| `elements.json` | All 13 books: 465 propositions, 132 definitions, 5 postulates, 5 common notions; 1,924 citation links |
| `extract_elements.py` | Extractor that produced `elements.json` from the Perseus encodings |
| `concordance.json` | Book I propositions mapped to GeoCoq and LeanEuclid |
| `formal/GeoCoq/` | GeoCoq `theories/Elements` (254 files), Beeson's formalisation of Euclid's own proofs |
| `formal/LeanEuclid/` | LeanEuclid `Book/` (48 files), System E, all Book I propositions |
| `archimedes.py` | Archimedes proposition by proposition: 43 propositions from nine works, 121 exact checks, each tied to its Greek locus |
| `graeca/` | 47 Greek mathematical works beyond the Elements: all of Archimedes, Eutocius, Apollonius' Conica I to IV, Pappus II to VIII, Euclid's Data, Optica, Catoptrica, Phaenomena, Sectio canonis, Theodosius, Autolycus, Aristarchus, Geminus, Ptolemy's Syntaxis, Hero, Nicomachus, Theon of Smyrna |
| `graeca.py` | Library over `graeca/`: works, passages, accent insensitive Greek search, Greek sources of each part (`graeca/links.json`) |
| `extract_graeca.py` | Extractor that produced `graeca/` from First1KGreek and the Open Greek Corpus |
| `ops.py` | Markdown reports used by the workflows (`verify`, `list`, `part`, `prop`, `search`, `ask`) |
| `site.html` | The published reader (single file HTML, data embedded) |

## Use

```bash
pip install sympy
python geometria.py
```

```python
import geometria, elementa
geometria.run("euclid-II-11")
elementa.get("I.47")
elementa.uses_parallel_postulate("I.29")
```

## Layers and verification

Each part keeps fact (what the source states), interpretation (modern formalisation, attribution, connections) and hypothesis apart. The Apollonius circle parts concern the project's working hypothesis `hyp-apollonius-last-supper` and are labelled as hypothesis, never as evidence.

Checks are marked by method: `symbolic` holds identically in general symbols; `instance` holds exactly for one concrete construction; `numeric` is confirmed to 50 digits and is not a proof.

The citation graph is read from Heath's bracketed references. Euclid's text cites nothing, so the graph and everything computed from it belong to the interpretive layer: it records Heath's reading of each proof.

## Archimedes, proposition by proposition

`archimedes.py` checks the enunciations of Archimedes' works one by one. Every entry gives the work and locus in `graeca/archimedes.json`, a summary of the Greek enunciation (factual layer), and checks. Before its checks run, each entry reads the Greek numeral at its locus and confirms it is the expected proposition: the encoding of De conoidibus skips 23, so from there its loci and Archimedes' numbers differ by one, and this guard catches any such shift.

| Work | Propositions checked |
| --- | --- |
| Dimensio circuli | 1, 2, 3 (all of Archimedes' rational bounds for the 96-gons, from the numbers in the Greek) |
| De sphaera et cylindro | I.13, 14, 16, 33, 34 with corollary, 42 (and 43), 44; II.2, 4, 8, 9 |
| De conoidibus et sphaeroidibus | 4, 21, 25, 27, 29 (and 31) |
| De lineis spiralibus | 18, 24, 25, 26, 27 |
| Quadratura parabolae | 19, 23, 24 |
| De planorum aequilibriis | I.6 (and 7), I.14 (and 13), II.8, II.10 |
| Ad Eratosthenem methodus | preface (hoof, two cylinders), 6, 9, 11 |
| Liber assumptorum | 4, 6, 8, 11, 14, 15 |
| Arenarius, Problema bovinum | the bound 10⁶³; the first part of the cattle problem solved, the second reduced to Amthor's Pell equation |

All 121 checks are symbolic or exact (instance); none rests on numerical agreement alone. They establish the stated results in modern terms (coordinates, integrals, exact arithmetic), not Archimedes' methods. Remarks that belong to interpretation are kept in each entry's note: Dimensio circuli 2 holds only with π replaced by 22/7 and so depends on proposition 3, which follows it; the Book of Lemmas survives only in Arabic; the reading of the cattle problem's second part as square and triangular numbers is a reading.

Not yet covered: the lemmas and inequalities of De sphaera et cylindro I.1 to 32, the oblique sections of De conoidibus, De corporibus fluitantibus (stability of the paraboloid; Books I.1, I.2, II.5, II.6 survive only in Moerbeke's Latin), the Stomachion, and the Method propositions that repeat results checked elsewhere.

## Greek texts beyond the Elements

`graeca/` holds the Greek of the mathematical authors as passages cited by the units of each encoding (mostly book.proposition), so that a part can show the words of its source.

| Group | Works | Transmission |
| --- | --- | --- |
| Archimedes | all 13 works in Mugler's edition (Paris 1970 to 1972), plus the Latin Liber assumptorum | tei |
| Eutocius | commentaries on Sphere and Cylinder, Measurement of the Circle, Plane Equilibria | tei |
| Apollonius | Conica IV (Heiberg) | tei |
| Apollonius | Conica I to III (Heiberg vol. 1), by printed page | ocr |
| Pappus | Collectio II to V (Hultsch vol. 1) | tei |
| Pappus | Collectio VI to VIII (Hultsch vols. 2 and 3), by printed page; Book VII holds the summaries of Apollonius' lost Tangencies and Plane Loci | ocr |
| Euclid | Data, Optica (two recensions), Catoptrica, Phaenomena, Sectio canonis, fragments; Marinus on the Data | tei |
| Spherics and astronomy | Theodosius, Autolycus, Aristarchus, Geminus, Ptolemy's Syntaxis | tei |
| Hero | Metrica, Dioptra, Stereometrica, De mensuris, Geodaesia, Geeponicus, Catoptrica | tei |
| Arithmetic | Nicomachus' Introductio, Theon of Smyrna | tei |

`tei` texts are curated encodings and keep the edition's numbering. `ocr` texts are machine transcriptions: unresolved readings stay as ⟦a ∥ b⟧, loci are printed pages, and nothing from them should be quoted before it is collated with the page of the edition. Both layers are Greek only; no translation is included, and any translation added later belongs to the interpretive layer.

Not yet available on GitHub in any form found: Conica V to VII (Arabic only), Pappus VIII's lost portions, Proclus' commentary on Euclid I, Diophantus in a curated encoding, English translations (Heath's Archimedes and Apollonius exist only as scans).

## Known gaps

* Newclid machine proofs exist for 4 of 22 parts. The III.31 run is not an independent proof: its decisive rule (r20) is III.31 itself.
* Formal proofs cover Book I only; no formalisation of Books II to XIII was found.
* GeoGebra sequences have not been tested in GeoGebra itself.
* Greek text is missing for I.30, II.7, X.6 and XII.7 in the source encoding.
* The build scripts that generated `site.html` and `parts.json` (metadata, figures, Newclid statements, page builder) were lost with a reset container and are not in this folder; their outputs are preserved in `parts.json` and `site.html`.

## On GitHub

* **Actions, Corpus Geometriae** (`.github/workflows/geometry.yml`): every push that touches `geometry/` reruns all checks and writes the table to the job summary. From the Actions tab, *Run workflow* runs any query (`verify`, `list`, `part`, `prop`, `search`) and shows the answer in the summary.
* **Issues** (`.github/workflows/geometry-ask.yml`): open an issue with the *Ask the corpus* form, or comment `/geo prop I.47`, `/geo part archimedes-spiral`, `/geo search gnomon`, `/geo works`, `/geo text archimedes.sphaera-cylindrus 1.33`, `/geo greek μέναιχμ`, `/geo archimedes`, `/geo arch SC.I.34` on any issue; a workflow replies with the text, the Greek, the citations, the formal proofs or the recomputed checks. Only the owner and collaborators can trigger it.
* **Pages**: the reader is published with the database at `/geometry/`.
* **Codespaces** (`.devcontainer/`): Python with sympy and JupyterLab, plus Node for the database scripts.

The same reports run locally: `python ops.py prop I.47`.

## Sources and licences

* Elements text: Perseus Digital Library encodings of Heiberg (Teubner 1883 to 1888) and Heath (Cambridge 1908), CC BY SA 4.0.
* GeoCoq: LGPL 3.0, commit `87e8f9c3bc9cb2f782b86153bcf8d5bac52d7ef6`, https://github.com/GeoCoq/GeoCoq
* LeanEuclid: MIT, commit `33a72c0fa83914202532998a2e7b8771295c3cc7`, https://github.com/loganrjmurphy/LeanEuclid (Murphy et al., ICML 2024).
* Greek texts beyond the Elements: OpenGreekAndLatin/First1KGreek (CC BY SA 4.0) and open-greek/open-greek-corpus release corpus-2026-10-28.2 (CC BY SA 4.0; public domain editions), commits recorded with every work in `graeca/`.
* Newclid 2.0.2 for the four machine proofs recorded in `parts.json`.
