# dane.gov.pl compliance gaps in Raport zbiorczy AED

Issue: APP-57
Date: 2026-11-22
Extends: `.ai/specs/2026-11-21-aed-aggregate.md` (APP-46), `aed-standard/` (APP-41)

## Problem

A juror found five gaps that cap the dane.gov.pl compliance score, verified by
L8 on a running main (2026-11-21):

1. The report declares a daily refresh, but `aed_refresh` reads only dated
   local snapshots, and local Compose runs no celery beat.
2. The OSM resource sits inside the CC BY 4.0 report dataset, so the portal's
   machine-readable licence says CC BY for ODbL data.
3. The report dataset has no category (API `categories: []`).
4. `operator_name` in all 74 municipal records is the publishing city office,
   while `aed-standard/README.md` says a record without a confirmed dysponent
   must not be accepted.
5. Data scope: no operator identifier; the gmina check is a rectangle, and the
   simplified L6 boundaries put 2 Legionowo points into Wieliszew.

## Outcome

1. **Live refresh.** For each of the 5 sources `aed_refresh` reads the public
   api.dane.gov.pl read-only (dataset, resources, institution, data file;
   timeout 20 s). If any request fails or the file is empty, it uses the
   committed snapshot. Each source records `origin` (`live` / `snapshot`) and
   the retrieval time; records carry it in `source_records[].retrieved_at` and
   `field_provenance.source_records`; the report dataset notes and the command
   output list it. A live file that differs from the committed one replaces the
   source dataset's resource file. OSM stays a dated snapshot.
   Honest frequency: a new Compose service `aed-beat` runs celery beat with
   only the AED tasks (`AED_BEAT_ONLY=1` keeps schedule entries whose task
   starts with `mcod.aed_`), so the declared "daily" refresh (03:30 UTC) runs
   whenever the stack runs.
2. **OSM dataset.** "Punkty AED z OpenStreetMap - Polska (ODbL 1.0)" is its own
   dataset of the operator institution (`ext_ident` `aed-osm-polska`); the
   existing resource `aed-osm-csv` moves into it. Licence: the portal has no
   ODbL choice, so the dataset uses the attribution condition with the custom
   text and the database-rights condition, both naming ODbL 1.0,
   "© OpenStreetMap contributors" and the ODbL URL. The report notes link the
   OSM dataset and the other way round. The report licence text no longer
   covers OSM.
3. **Category.** Report and OSM datasets get the category with code `HEAL`
   ("Zdrowie"), as the wizard does.
4. **Operator.** Municipal records: `operator_name` = `nieustalony`, quality
   flag `operator_unconfirmed`, city office in
   `source_records[].publisher_name`. OSM records: `operator` tag kept as a
   candidate (else `nieustalony`), flag `operator_unconfirmed` on all.
   `aed-standard/validate.py` (one rule set, used by the wizard): the
   placeholder requires the flag; a record with a `dysponent:` source must not
   use the placeholder or the flag.
5. **Data scope.** aed-standard gets optional `operator_regon` (9 or 14 digits,
   GUS check digit) in schema, field dictionary xlsx, template, example,
   mappings and validator tests (44 fields). The gmina check uses exact PRG
   boundaries of the four dysponent gminy (GUGiK ULDK, committed in
   `backend/data/aed/prg/`, same register as L6's simplified file). A point
   inside its dysponent's gmina gets that 7-digit `terc` (dated register, so
   Legionowo's 6-digit code no longer needs `teryt_incomplete`); a point that
   lies outside it, also after an axis swap, keeps `outside_expected_area` and
   no published position.

## Non-goals

- Confirming real operators or REGON numbers.
- New sources, live OSM download, changes to portal design.
- Changing L6's counters (data contract change reported to the coordinator).

## Acceptance

| # | Criterion | Check |
|---|---|---|
| C1 | Live fetch used when the API answers; snapshot when it fails; origin and time recorded per source | `test_compliance` (mocked HTTP) |
| C2 | OSM resource in its own dataset with ODbL text; report dataset text links OSM and no longer claims OSM | `test_compliance` publish test |
| C3 | Report and OSM datasets have category HEAL | `test_compliance` publish test |
| C4 | Municipal records: placeholder + flag + publisher_name; validator rejects placeholder/flag for `dysponent:` sources | `test_compliance`, `aed-standard/tests/test_validate.py` |
| C5 | `operator_regon` in all aed-standard artefacts, check digit enforced | `aed-standard/tests` (contract + validator) |
| C6 | PRG gmina check: all 24 Legionowo points get terc 1408011; a point outside its gmina is withheld | `test_compliance` |
| C7 | `aed-beat` keeps only AED schedule entries | `test_app_config` |

## Verification

- `python3 -B -m unittest discover -s aed-standard/tests`
- Validation gate (`AGENTS.md`), local `aed_refresh` run with network and with
  the API unreachable.
