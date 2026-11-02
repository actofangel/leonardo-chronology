# Leonardo Chronology

A working research platform for the *Identity of Leonardo da Vinci* project: Leonardo's places, works, people and events from 1452 to 1519, with the papacy and the wider history of the period, on one time scale.

Every record carries two independent labels.

* **Evidence layer** (`tier`): what kind of claim it is. `D` documented, `S` scholarly dating or attribution, `T` later tradition.
* **Review status**: how far this site has checked it. `pending`, `flagged`, `disputed`, `corrected`, `verified`, `rejected` (not accepted).

The records were first entered from model recall. They therefore stay **pending** until checked against a source of an admitted type. Nothing in this repository should be read as verified unless its review entry says so and cites an admitted source.

## Files

| File | Role |
| --- | --- |
| `index.html` | The page, single file. Holds the base records (`PLACES`, `WORKS`, `PEOPLE`, `EVENTS`, `POPES`, `HISTORY`) and the app. |
| `reviews.json` | Review layer: status, flags, proposed corrections, sources and history per record id. |
| `extra.json` | New records added after the base draft. They start as pending. |
| `scripts/validate.mjs` | Enforces the update protocol. Run before every commit. |
| `.github/workflows/pages.yml` | Runs the validator on every push and pull request, and deploys `main` to GitHub Pages. |

## Update protocol

1. Admitted source types: `edition` (critical edition, e.g. Villata, Beltrami), `catalogue` (catalogue raisonné, e.g. Marani, Zöllner), `ms_study` (codicological or manuscript study, e.g. Pedretti), `monograph` (peer reviewed), `archive_publication`. The types `web`, `model_recall` and `other` can raise a flag or propose a change. They cannot verify.
2. A correction goes under `proposed` and is not applied to the record until the researcher accepts it. Accepting means editing the base data, setting the status to `corrected` and adding a history line.
3. History lines are added, never edited or removed. CI compares against the previous commit.
4. New records go in `extra.json` with a `lane` and the same fields as existing records.
5. Status fields never go on the records themselves. They live only in `reviews.json`.
6. Notation: no dash characters of any kind in data text.

The chronology does not include the project's working hypotheses, such as the Apollonius circle in the Last Supper or deliberate Latin lexical overlap. They belong on a separate hypothesis layer.

## Local use

```bash
node scripts/validate.mjs
```

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>. Opening `index.html` directly from disk shows the base records only, because browsers block reading the JSON files from `file://`.
