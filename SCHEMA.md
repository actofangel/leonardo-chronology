# Data model (ldv-entity/1)

The database is a folder of JSON files under `data/`, one file per entity. The file name is the entity id plus `.json`. Everything else in the repository (the chronology page, the entity browser, `db.json`) is generated from these files by `scripts/build.mjs`.

## Folders and entity types

| Folder | `type` | Id prefix (new entities) | What it holds |
| --- | --- | --- | --- |
| `data/persons/` | `person` | `pe-` | People, including popes (`subtype: "pope"`) |
| `data/places/` | `place` | `geo-` | Towns, buildings, institutions, collections |
| `data/works/` | `work` | `w-` | Paintings, drawings, cartoons, sculpture projects, engineering, maps |
| `data/manuscripts/` | `manuscript` | `ms-` | Codices, notebooks, collections of sheets |
| `data/events/` | `event` | `e-` | Dated events, residences (`subtype: "residence"`), historical context (`subtype: "context"`) |
| `data/sources/` | `source` | `src-` | Bibliographic and archival sources |
| `data/hypotheses/` | `hypothesis` | `hyp-` | Working hypotheses and scenarios |

Ids are lowercase ASCII, words joined by single hyphens, stable forever. Records migrated from the first chronology keep their old ids (`pl-`, `po-`, `h-` included).

## Common fields

```json
{
  "id": "w-ermine",
  "type": "work",
  "subtype": "painting",
  "label": "Lady with an Ermine",
  "variants": ["Portrait of Cecilia Gallerani", "Dama con l'ermellino"],
  "summary": "One or two sentences, factual layer only.",
  "relations": [ { "rel": "depicts", "target": "pe-cecilia", "claim": "c3" } ],
  "claims": [ ],
  "timeline": { },
  "review": { },
  "open_questions": [ "Question that research has not yet answered." ]
}
```

Only `id`, `type`, `label` are required. `summary` must not contain interpretation. Interpretations are claims.

### Type specific fields (all optional)

* person: `born`, `died` (short display strings, e.g. "c.1480", "19 January 1524"), `roles` (array)
* place: `modern_name`, `region`, `country`, `coords` `{ "lat": 45.4659, "lon": 9.1709 }`, `within` (id of the containing place)
* work: `medium`, `support`, `dimensions`, `current_location` (place id or text), `inventory` (museum number), `catalogue` (array of `{ "src": "src-zollner-2003", "number": "XIX" }`), `manuscript` (manuscript id, for drawings on a codex sheet), `folio`
* manuscript: `holding` (place id or text), `shelfmark`, `folios` (count or text), `date_range` (`{ "start": 1478, "end": 1519 }`), `contents` (array of short strings), `history` (array of short provenance strings)
* source: `source_type` (see admission), `citation` (full), `short` (e.g. "Villata 1999"), `url`, `language`
* hypothesis: `status` (always `"working_hypothesis"` or `"speculation"`), `statement`, `assumes` (array of `"entity#claim"` refs), `supports`, `against`, `falsified_if` (arrays of strings), `proposed_by`

## Classification

Works and manuscripts carry a `classification` block whose values come from the controlled vocabularies in `data/vocab/classification.json`. The validator rejects any other value.

```json
"classification": {
  "form": "painting",
  "technique": ["oil"],
  "support": "panel_walnut",
  "condition": "extant",
  "subject": ["portrait", "animal"],
  "basis": "Where the values come from, e.g. the holding institution's record, or 'model recall, to check'."
}
```

* Works: `form` (one value; grouped as Paintings, Drawings, Sketches, Designs, Projects), `technique` (several), `support`, `condition`, `subject` (several).
* Manuscripts: `ms_form` (notebook, pocket notebook, compiled codex, collection of sheets, compilation by another hand), `support`, `condition`, `subject` (several).
* Form, technique, support and condition describe the object and should rest on an observation or a documented description. Subjects are an editorial finding aid, not a claim about meaning.
* Anything contested stays out of the classification and goes into claims: attribution, a sheet's role as preparatory for a given work, the identity of a sitter, the dating.
* Classification values for a heavily debated object (for example, whether a work is a painting by Leonardo at all) are still descriptive: the Salvator Mundi is classified as a painting on walnut panel; its attribution is a set of claims.

## Claims

A claim is one assertion about the entity, with its own layer, sources and status. Competing datings or attributions are separate claims about the same `about` key.

```json
{
  "id": "c2",
  "about": "date",
  "value": { "text": "c.1489 to 1491", "start": 1489, "end": 1491 },
  "layer": "interpretation",
  "grade": "strong_interpretation",
  "status": "pending",
  "statement": "Dated c.1489 to 1491 on grounds of style and the sitter's time at court.",
  "sources": [
    { "ref": "src-marani-2000", "loc": "cat. no. to locate" },
    { "type": "web", "cite": "Czartoryski Museum, collection page.", "url": "https://..." }
  ],
  "check_in": ["Zöllner 2003, catalogue entry"],
  "alternative_to": ["c1"],
  "bearing": "Optional: what this claim changes elsewhere."
}
```

* `about`: `date`, `attribution`, `location`, `current_location`, `medium`, `identity`, `born`, `died`, `relation`, `provenance`, `residence`, `content`, `timeline` (migrated chronology entry), or another short key.
* `layer`: `fact` (what a document or object states or shows), `interpretation` (dating by style, attribution, identification, reading), `hypothesis` (belongs to a working hypothesis).
* `grade` (optional): `fact`, `strong_interpretation`, `working_hypothesis`, `speculation`.
* `status`: `pending`, `verified`, `disputed`, `rejected`.
* `sources`: either a reference to a source entity (`ref` plus `loc`, the locator: document number, page, folio, catalogue number) or an inline source (`type`, `cite`, `url`).
* A `loc` must never be guessed. If the exact number is unknown, write `"to locate"` and add the edition to `check_in`.

## Source admission

| `type` / `source_type` | Admitted (can verify) |
| --- | --- |
| `edition` (critical documentary edition: Villata, Beltrami) | yes |
| `catalogue` (catalogue raisonné: Marani, Zöllner) | yes |
| `ms_study` (codicological study: Pedretti) | yes |
| `monograph` (peer reviewed) | yes |
| `archive_publication` (published archival document) | yes |
| `primary` (the manuscript or object itself, cited by folio or inventory) | yes |
| `other` (reference works, museum catalogue pages, journal pieces not yet classed) | no |
| `web` | no |
| `model_recall` | no |

A claim is `verified` only with at least one admitted source. The validator enforces this.

## Precedence

When several claims share an `about`, the build picks one to display, in this order:

1. status: `verified` over `pending` over `disputed`; `rejected` is never picked
2. layer: `fact` over `interpretation` over `hypothesis`
3. best source: `primary`, `edition`, `archive_publication` over `catalogue`, `ms_study` over `monograph` over `other` over `web` over `model_recall`
4. order in the file

The losing claims stay visible as alternatives. A scenario (see below) can override this order.

## Timeline and review (chronology view)

`timeline` holds the display fields of the chronology page: `lane` (`places`, `works`, `people`, `events`, `popes`, `history`), `kind`, `start`, `end`, `date`, `tier` (`D`, `S`, `T`), `place`, `text`, `basis`. An entity with a `timeline` block appears on the chart.

`review` holds the chronology's review layer: `status`, `flags`, `proposed`, `note`, `sources`, `history`. History lines are append only.

## Hypotheses, scenarios and branches

* A hypothesis entity names the claims it assumes. Building with `--scenario hyp-x` lets those claims win over the normal precedence, so the chronology and `db.json` show the world as the hypothesis would have it. The default build never applies a scenario.
* Larger alternative readings live on git branches named `hyp/<slug>`, or in forks. The validator runs on every branch, so a fork stays a valid database. Merging into `main` needs the same evidence rules as any other change.
* Claims that belong only to a hypothesis use `layer: "hypothesis"` and never appear as fact in the default view.

## Notation

No dash characters of any kind in text (em dash, en dash, horizontal bar, minus sign, doubled hyphen). Write ranges as "1478 to 1482". Quote primary sources in the original language, with a translation where needed; translations are interpretations.
