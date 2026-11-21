# dane.gov.pl compliance gaps - execution plan

Issue: APP-57
Run: app57-20261121T231639Z
Branch: feat/aed-compliance (from origin/main 163ae18)
Source doc: .ai/specs/2026-11-22-aed-compliance.md

## Steps

- [x] 1. aed-standard: operator_regon (schema, xlsx, template, example, mappings, docs), flags operator_unconfirmed / operator_from_location, validator rules + tests
- [x] 2. Aggregator: live api.dane.gov.pl fetch with snapshot fallback, PRG gmina check + terc, operator from location, merge rule
- [x] 3. Publish: OSM dataset (ODbL text), category HEAL, cross-links, refresh summary; aed-beat service
- [x] 4. Demo dysponenci (seed_aed_demo) through the wizard path
- [ ] 5. Tests, validation gate, local run (live and offline), review, PR, merge

## Progress

- 45433fe: aed-standard part. RED on main for the new validator tests (operator_regon unknown field; placeholder rule missing), GREEN after.
- Aggregator/publish/demo tests in test_compliance.py were written with the code (no separate RED run; on main they fail at import of the new functions).
