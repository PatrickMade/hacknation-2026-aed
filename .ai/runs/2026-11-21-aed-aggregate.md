# Raport zbiorczy AED - execution plan

Issue: APP-46
Run: app46-20261121T173139Z
Branch: feat/aed-aggregate (stacked on feat/portal-local-stack 090d7b09 + origin/main 4e6c518)
Source doc: .ai/specs/2026-11-21-aed-aggregate.md

Goal, scope, non-goals and risks: see the spec.

## Steps

- [x] 1. Snapshots of the five sources and OSM PL in backend/data/aed/sources/
- [x] 2. Mapping, dedup, validation and publication app backend/mcod/aed_aggregate/
- [x] 3. Tests for mapping, dedup, provenance and publication
- [x] 4. Local run: seed_jury + aed_refresh, API rows, map preview
- [x] 5. Validation gate, review, PR (#8)

## Progress
- 2026-11-21 UTC 32ff905 (rebased; was 332d342): snapshots, mapping, dedup, publication, command, Celery task.
- 3281a46 (rebased; was ef1d203): report column types and declared empty-cell sign; local run: 74 records, CSV map + /1.4 rows, OSM 18298 points.
- Independent review (request changes) fixed: OSM contact scrubbing, same-source merge guard, swapped coordinates as unknown method, fail-closed licence, Celery local guard, tests for publish/replace/build failure; standard deviations recorded in the spec.
- Map tab blank in the local frontend (leaflet require in frontend/src/app/services/leflet.service.ts); decision requested from the coordinator; with a local 1-line import fix the map shows the 73 placed records.
- a36cd82: review round 1 fixes; PR #8 opened after rebase on main 03f4f52; CI green.
- Independent review (separate session) requested changes: licence notice for committed source snapshots, aggregator tests in the CI gate, narrower phone filter, plan references. Fixed in the next commit.
