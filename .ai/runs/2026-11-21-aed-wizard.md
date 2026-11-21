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
4. [ ] Przeglądarka i pełny gate (zrobione 10a999a); PR po scaleniu PR #3, niezależny review, merge.

## Evidence
- Commits: 193570b spec/plan, 60897db wizard + validator, 10a999a table schema preset + panel branding.
- Tests written alongside the code, not test-first; no RED evidence is claimed. `mcod.aed_wizard`: 13 tests OK (8 mapping/validation, 5 views/publication/public check) in an isolated Compose project `aed-l5`.
- Conversion trial on real snapshots of the municipal files (Krosno CSV, Marki double-quoted CSV with swapped axes, Legionowo CSV, Przemyśl GeoJSON): validator errors 0 after mapping; Marki 7 axis errors until the swap option, 0 after.
- Upstream migration order: an app label sorting first that depends on organizations breaks `organizations.0018` (SQL on counters tables, undeclared). The publication record therefore stores plain ids; migration has no dependencies; full `migrate` exits 0.
- Browser (headless Chrome, isolated stack on 127.0.0.1:8101 with a test-only cookie-domain override): krosno.agent sees only Krosno; mapping suggested correctly; report 0 errors for 21 records; publication created dataset 1 (Zdrowie, keywords AED/defibrylator/zgodny ze standardem AED, CC BY 4.0, monthly). Resource 2 (after schema preset): format csv, openness 3, 21 rows in API 1.4 `/resources/2/data`, visualization types map+table. Resource 1 (before the fix) failed portal table indexing on an empty integer-guessed column; fixed by the preset schema.
- Public validator anonymous: Krosno raw file -> header error + hint (5 recognisable columns); example.csv -> compliant. No horizontal scroll at 500 px (headless minimum); 360 px not measured.
- Full gate on 10a999a (Compose commands with COMPOSE_PROJECT_NAME=aed-l5): all 5 commands exit 0; test_jury_seed 2 tests OK.
- Not verified: pickup by the L4 aggregator (its code is not available yet); production hostnames admin.mcod.local in the shared stack.
