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

## Known gaps

* Newclid machine proofs exist for 4 of 22 parts. The III.31 run is not an independent proof: its decisive rule (r20) is III.31 itself.
* Formal proofs cover Book I only; no formalisation of Books II to XIII was found.
* GeoGebra sequences have not been tested in GeoGebra itself.
* Greek text is missing for I.30, II.7, X.6 and XII.7 in the source encoding.
* The build scripts that generated `site.html` and `parts.json` (metadata, figures, Newclid statements, page builder) were lost with a reset container and are not in this folder; their outputs are preserved in `parts.json` and `site.html`.

## On GitHub

* **Actions, Corpus Geometriae** (`.github/workflows/geometry.yml`): every push that touches `geometry/` reruns all checks and writes the table to the job summary. From the Actions tab, *Run workflow* runs any query (`verify`, `list`, `part`, `prop`, `search`) and shows the answer in the summary.
* **Issues** (`.github/workflows/geometry-ask.yml`): open an issue with the *Ask the corpus* form, or comment `/geo prop I.47`, `/geo part archimedes-spiral`, `/geo search gnomon` on any issue; a workflow replies with the text, the Greek, the citations, the formal proofs or the recomputed checks. Only the owner and collaborators can trigger it.
* **Pages**: the reader is published with the database at `/geometry/`.
* **Codespaces** (`.devcontainer/`): Python with sympy and JupyterLab, plus Node for the database scripts.

The same reports run locally: `python ops.py prop I.47`.

## Sources and licences

* Elements text: Perseus Digital Library encodings of Heiberg (Teubner 1883 to 1888) and Heath (Cambridge 1908), CC BY SA 4.0.
* GeoCoq: LGPL 3.0, commit `87e8f9c3bc9cb2f782b86153bcf8d5bac52d7ef6`, https://github.com/GeoCoq/GeoCoq
* LeanEuclid: MIT, commit `33a72c0fa83914202532998a2e7b8771295c3cc7`, https://github.com/loganrjmurphy/LeanEuclid (Murphy et al., ICML 2024).
* Newclid 2.0.2 for the four machine proofs recorded in `parts.json`.
