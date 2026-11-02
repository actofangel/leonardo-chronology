# Contributing

This database is meant to be checked, corrected and argued with. Every contribution is a pull request, and every pull request is validated by CI with the same rules.

## Kinds of change

| You want to | Do this | Branch name |
| --- | --- | --- |
| Verify a claim | Add an admitted source with an exact locator to the claim and set `status` to `verified` | `verify/<entity-id>` |
| Report a doubt | Add a `disputed` claim, or a flag in the entity's `review` block, with your reason and source | `review/<entity-id>` |
| Correct a value | Add a new claim with the corrected value and `alternative_to` the old one. Set the old claim to `rejected` only when the new one is verified | `fix/<entity-id>` |
| Add an entity | New file in the right `data/` folder, following SCHEMA.md | `add/<entity-id>` |
| Work on a hypothesis | See below | `hyp/<slug>` |
| Import a research batch | Put the files in `research/incoming/<batch>/`, then run `node scripts/merge-incoming.mjs research/incoming/<batch>` | `research/<batch>` |

Never delete a claim or edit a review history line. CI compares against the previous commit and fails if either happens.

## Working on hypotheses

There are two levels, and they can be combined.

**Inside the data (scenarios).** A hypothesis entity in `data/hypotheses/` states the hypothesis, its scope, the evidence for and against, and the conditions under which it would fail (`falsified_if`, required). Claims that only hold under the hypothesis are written on the entities they concern with `"layer": "hypothesis"`, and listed in the hypothesis's `assumes`. The default build never lets them win. A scenario build (`--scenario <id>`) lets them win, so the chronology and the browser show the world as the hypothesis would have it. Scenario builds are published under `scenarios/<id>/` and are always labelled as such.

**On git (branches and forks).** A larger alternative reading, for example a different chronology of a whole period or a different attribution of a group of works, is developed on a branch named `hyp/<slug>` or in a fork. The validator runs there as on `main`, so the branch stays a valid database and can be built and compared. A hypothesis branch is merged into `main` only as hypothesis claims and a hypothesis entity, never by overwriting factual claims.

To compare two branches:

```bash
git diff main..hyp/<slug> -- data/
```

## Before opening a pull request

```bash
node scripts/validate.mjs
```

```bash
node scripts/build.mjs
```

Both must pass. Use `--strict` to also treat warnings (such as links to entities that do not exist yet) as errors.

## Style

* English for summaries and statements. Quote primary sources in the original language (Italian, Latin, French) with an English translation; a translation is itself an interpretation.
* No dash characters of any kind. Write ranges as "1478 to 1482".
* Locators are never guessed. If you do not have the document number, folio or catalogue number in front of you, write "to locate" and name the edition in `check_in`.
