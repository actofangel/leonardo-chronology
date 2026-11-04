# Leonardo Database

An open research database for the *Identity of Leonardo da Vinci* project. It holds the people, places, works, manuscripts, events and sources of Leonardo's life as individual records, each made of **claims** that carry their own evidence layer, sources and review status. The chronology is one view generated from the database; the entity browser is another.

The repository is the database. Every record is a JSON file under `data/`, so every change is a reviewable diff, every alternative reading can live on a branch or a fork, and the full history of what was claimed, by whom and on what evidence is kept by git.

## Status of the content

Most records were first entered from model recall or from web research. They are **pending**: they say where to check, not what is established. A claim becomes `verified` only when it cites a source of an admitted type (critical edition, catalogue raisonné, codicological study, peer reviewed monograph, published archival document, or the primary object cited by folio or inventory). The validator refuses anything else.

## Layout

| Path | Contents |
| --- | --- |
| `data/persons/`, `places/`, `works/`, `manuscripts/`, `events/` | One file per entity |
| `data/sources/` | Bibliography and archival sources, each typed for admission |
| `data/hypotheses/` | Working hypotheses with their test conditions; scenarios for alternative readings |
| `data/views/chronology.json` | Display settings for the chronology (era bands) |
| `site/explorer.html`, `site/chronology.html` | Page templates (single file HTML) |
| `scripts/validate.mjs` | Enforces the schema and the research protocol |
| `scripts/build.mjs` | Builds `dist/`: entity browser, chronology, `db.json`, scenario views |
| `scripts/merge-incoming.mjs` | Additive merge of research batches into `data/` |
| `research/` | Research briefs, incoming batches, reports and unapplied review patches |
| `geometry/` | Corpus Geometriae: classical constructions as Python and GeoGebra with sympy checks, the complete Elements, and Book I formal proofs (see `geometry/README.md`) |
| `SCHEMA.md` | The data model, source admission and precedence rules |
| `CONTRIBUTING.md` | How to add evidence, propose corrections, and work on hypotheses in branches |

## Use

```bash
node scripts/validate.mjs
```

```bash
node scripts/build.mjs
```

```bash
cd dist && python3 -m http.server 8000
```

Open <http://localhost:8000> for the entity browser and <http://localhost:8000/chronology.html> for the chronology. No dependencies beyond Node 20 or later.

To see the database as a working hypothesis would have it:

```bash
node scripts/build.mjs --scenario hyp-apollonius-last-supper --out dist/scenarios/hyp-apollonius-last-supper
```

## Principles

1. **Layer purity.** Facts (what a document or object states or shows), interpretations (datings by style, attributions, identifications, readings) and hypotheses are separate claims, never mixed in one statement.
2. **Source admission.** Only admitted source types can verify. Web pages, reference works and model recall may raise questions.
3. **Nothing is deleted.** A wrong claim is set to `rejected` with a reason; review history is append only. CI checks both against the previous commit.
4. **Precedence is explicit.** When claims compete, a fixed rule (SCHEMA.md) decides which is shown first, and the others stay visible.
5. **Hypotheses are held apart.** The project's working hypotheses live in `data/hypotheses/` with the conditions under which they would fail, and only appear in scenario builds.
6. **Notation.** No dash characters in data text.

Published with GitHub Pages on every push to `main`. Scenario views are published under `scenarios/<hypothesis id>/`.
