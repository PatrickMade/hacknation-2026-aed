# Kreator dysponenta AED
Issue: APP-43
Source doc: .ai/specs/2026-11-21-aed-wizard.md
Route: agreed delivery
RUN_ID: cc086900-1ee8-48d1-9e65-5cd38d5015c4
Evidence: zakres z briefu koordynatora (wave 2, L5).

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] Spec i plan.
2. [x] Odczyt plików, mapowanie, walidacja przez aed-standard, diagnostyka; testy.
3. [x] Widoki kreatora, publikacja, publiczny walidator, menu, URL, Compose; testy.
4. [ ] Przeglądarka i pełny gate (przed rebase); PR #5 po scaleniu PR #3; niezależny review (APPROVE na f35a270); merge przez merge gate.

## Evidence
- Commits after the rebase onto main 03f4f52 (pre-rebase IDs in brackets): a8422ea spec/plan (193570b), b2d9f6b wizard + validator (60897db), adb83a9 table schema preset + panel branding (10a999a), a0a2359 redirects, f35a270 review fixes.
- Tests written alongside the code, not test-first; no RED evidence is claimed. `mcod.aed_wizard`: 13 tests OK at 10a999a (8 mapping/validation, 5 views/publication/public check); 16 OK after review fixes (redirect handling, 3xx without Location, no temp file left by the public check) in an isolated Compose project `aed-l5`.
- Conversion trial on real snapshots of the municipal files (Krosno CSV, Marki double-quoted CSV with swapped axes, Legionowo CSV, Przemyśl GeoJSON): validator errors 0 after mapping; Marki 7 axis errors until the swap option, 0 after.
- Upstream migration order: an app label sorting first that depends on organizations breaks `organizations.0018` (SQL on counters tables, undeclared). The publication record therefore stores plain ids; migration has no dependencies; full `migrate` exits 0.
- Browser (headless Chrome, isolated stack on 127.0.0.1:8101 with a test-only cookie-domain override): krosno.agent sees only Krosno; mapping suggested correctly; report 0 errors for 21 records; publication created dataset 1 (Zdrowie, keywords AED/defibrylator/zgodny ze standardem AED, CC BY 4.0, monthly). Resource 2 (after schema preset): format csv, openness 3, 21 rows in API 1.4 `/resources/2/data`, visualization types map+table. Resource 1 (before the fix) failed portal table indexing on an empty integer-guessed column; fixed by the preset schema.
- Public validator anonymous: Krosno raw file -> header error + hint (5 recognisable columns); example.csv -> compliant. No horizontal scroll at 500 px (headless minimum); 360 px not measured.
- Full gate on the pre-rebase commit 10a999a (old base 090d7b0, Compose with COMPOSE_PROJECT_NAME=aed-l5): all 5 commands exit 0; test_jury_seed 2 tests OK. CI on the current head supersedes it.
- Not verified: pickup by the L4 aggregator (its code is not available yet); production hostnames admin.mcod.local in the shared stack.
- Review 1 (session ended without a record) found URL import not following redirects; fixed in a0a2359 (checked hops, max 5).
- Review 2 (CHANGES_REQUESTED on a0a2359, record https://github.com/PatrickMade/hacknation-2026-aed/pull/5#pullrequestreview-6007298156): stale spec line on map roles fixed; description and institution title escaped; public XLSX read capped at 20 000 rows; response closed on errors and a 3xx without Location refused; temp-file test added. Not changed: wizard tests stay outside `validation.commands` (shared gate list, follow-up proposal); menu entry visibility for staff without an institution (nit).
- Review 3 (APPROVE on f35a270, record https://github.com/PatrickMade/hacknation-2026-aed/pull/5#pullrequestreview-6007351082) minors addressed afterwards: XLSX read capped at 200 columns (rows padded to the last cell could exhaust memory on the anonymous page), urllib3 read errors shown as form errors, spec wording on map roles/caps, multi-line description kept with linebreaks. 16 tests OK (column cap asserted in the XLSX test).
- Coordinator decision (option A): reader of published profile resources added to `aed_aggregate/sources.py` (`published_records()`), passed by `refresh()` into `build()`; test `aed_wizard/tests/test_aggregate_pickup.py` (wizard publication -> 2 records in the report). Wizard tests added to the gate command next to `mcod.aed_aggregate` (config, AGENTS, SDLC, README; AGENTS pin refreshed). On top of PR #8 head 28e277b: `mcod.aed_wizard mcod.aed_aggregate test_jury_seed` 39 tests OK.
- Review of dfb0eb7 (CHANGES_REQUESTED, record https://github.com/PatrickMade/hacknation-2026-aed/pull/5#pullrequestreview-6007604014) fixed: reader takes only the newest published resource per dataset; report keeps the dysponent's `aed_id` (`aggregate.deduplicate`, provider records only); files whose `source_id` is not `dysponent:<publishing institution>` and unreadable files are skipped and listed in the refresh result; spec tag line corrected. Gate test command (`test_jury_seed`, `mcod.aed_aggregate`, `mcod.aed_wizard`): 41 tests OK.
