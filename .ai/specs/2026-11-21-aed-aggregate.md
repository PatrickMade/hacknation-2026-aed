# Raport zbiorczy AED (agregator)

Issue: APP-46
Date: 2026-11-21
Depends on: `aed-standard/` (APP-41), local portal and `seed_jury` (APP-42)

## Problem

Five dane.gov.pl datasets describe AEDs (Krosno 3624, Marki 4955, Przemyśl
4581, Warszawa 39512, Legionowo 40593), each in a different layout. Nobody can
download one national, machine-readable AED dataset. The jury checks the
prototype in a local copy of the dane.gov.pl portal.

## Outcome

One management command, `aed_refresh`, run after `seed_jury`:

1. Loads each source as a dataset of its seeded institution (`jury-<slug>`)
   from a dated snapshot in `backend/data/aed/sources/<slug>/`: the original
   file, the original dane.gov.pl dataset/resource/institution metadata, the
   source URL and the retrieval time. Warszawa has no anonymous AED payload
   (`aed-standard/mappings.md`), so its dataset keeps the original catalogue
   link only and contributes no records.
2. Maps every source record to the AED profile following
   `aed-standard/mappings.csv`, validates each record with the functions of
   `aed-standard/validate.py` and the final file with its `validate()`; no
   second copy of the rules.
3. Deduplicates: records with the same namespaced source identity merge;
   records closer than 25 m merge only when their normalised address and name
   match; otherwise both get `duplicate_candidate`.
4. Keeps per-record provenance in `source_records` (source id, source record
   key, file URL, retrieval time, licence, resource id, data date, mapped
   original values, field-level notes) and names the publishing institution of
   the source dataset in `operator_name`, marked in `field_provenance` as the
   responsible party to confirm.
5. Flags quality issues per record: `encoded_csv` (Marki), `suspected_axis_swap`
   (axes swapped back only when the swapped point lies in the source's expected
   area), `outside_expected_area` (coordinates removed from the published row,
   originals kept in provenance), `teryt_incomplete` (Legionowo 6-digit TERC),
   `duplicate_candidate`.
6. Publishes the dataset "Raport zbiorczy AED" of the portal-operator
   institution (model: DGA raport zbiorczy, dataset 4354) with:
   - CSV resource in the AED profile with map preview (`l` = longitude,
     `b` = latitude, `label` = name, per `x-map` in `schema.json`);
   - GeoJSON resource with the same records;
   - separate CSV resource "Punkty AED z OpenStreetMap - Polska" (OpenAEDMap
     PL export of OSM, ODbL 1.0, "© OpenStreetMap contributors"), mapped to the
     same profile without phone, e-mail or editor data.
7. Runs the portal's own resource file and data pipeline synchronously, so
   the table, map and `/1.4/resources/<id>/data` rows exist when the command
   ends.
8. The Celery task `mcod.aed_aggregate.tasks.aed_refresh_task` runs the same
   refresh; a daily beat entry is registered. Demo: run the command on demand
   (compose has no beat service).

Repeat runs are idempotent: datasets and resources are found by `ext_ident`,
changed files replace the main file of the same resource, `aed_id` is a UUIDv5
of the namespaced source key, so it is stable across runs.

## Non-goals

- Provider wizard and validator page (L5, APP-43), incident reports (L7),
  campaign page (L6).
- Publishing scraped gov.pl records as official data.
- Changing portal design or content outside AED datasets.
- Live download of sources during the command: the snapshot is the input;
  refreshing the snapshot is a separate, dated step.

## Decisions and limits

- The portal licence selector has no ODbL. The report dataset is CC BY 4.0
  (Marki and Warszawa are CC BY 4.0, the rest CC0); its custom licence text and
  the OSM resource title/description state that the OSM resource is ODbL 1.0,
  not CC BY 4.0.
- Legionowo has no record ID. The source record key is a generated local key
  (hash of the original row), labelled as such in provenance, until the
  provider assigns IDs.
- Krosno/Marki addresses are split with a conservative pattern; an address
  that does not match stays only in `original_values`.
- Operating status, access, hours and verification stay `unknown`: the sources
  do not prove them.
- OSM `operator` is a candidate only; a missing operator is published as
  "nieustalony (OpenStreetMap)".

## Acceptance

| # | Criterion | Check |
|---|---|---|
| A1 | After `seed_jury` + `aed_refresh`: 5 source datasets in `jury-*` institutions, report dataset with CSV, GeoJSON and OSM resources | `test_aed_aggregate` DB test; local run output |
| A2 | Report CSV passes `aed-standard/validate.py` | test + command check (refuses to publish otherwise) |
| A3 | Map preview: report CSV resource `has_map`, schema geo `l`/`b`/`label` | local run, `/1.4/resources/<id>` and portal page |
| A4 | `/1.4/resources/<id>/data` returns rows | local API call |
| A5 | Mapping, dedup and provenance covered by tests | `mcod.aed_aggregate.tests` |

## Verification

- `docker compose run --rm manage python manage.py test mcod.aed_aggregate --noinput --keepdb`
- Local run: `seed_jury`, `aed_refresh`, API calls, portal page screenshot.
- Project validation gate (`AGENTS.md`).
