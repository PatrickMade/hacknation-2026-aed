# Zgłoszenia AED, QR i "Najbliższy AED"
Issue: APP-45
Run: fa888f78-a1e1-4d0b-a148-d314c6b53d73
Source doc: .ai/specs/2026-11-21-aed-reports.md
Route: agreed delivery (wave 2 lane L7, coordinator brief)
Base: origin/feat/portal-local-stack 090d7b09 (PR #3); rebase --onto origin/main after it merges.

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] Backend: test RED, modele, migracja, API, panel, reguły, e-mail (GREEN) - 9a0380d.
2. [x] Koder QR, endpoint SVG, podgląd w panelu - 9a0380d.
3. [x] Komendy load_aed_devices, seed_aed_showcase, dane demo - 9a0380d.
4. [x] Trasa frontendu /pl/aed/:aedId i weryfikacja w przeglądarce - 11f4f5d.
5. [ ] Weryfikator źródeł, README, oświadczenie AI, pełny gate, review, PR #7, merge.

## Evidence
- RED (empty route table, app installed): Django runner, 8 tests, failures=5 errors=2: 404 != 200/201/400 and `Unknown command: 'load_aed_devices'`.
- Migration ordering: depending on the latest organizations migration made Django apply organizations.0018 (raw SQL on counters tables, undeclared upstream dependency) before counters on a fresh DB; the migration now depends on counters.0002, which already has organizations.0001 as an ancestor. Fresh `migrate` on an isolated DB exited 0.
- QR encoder: byte-identical to qrcodegen 1.8.0 for 5 payloads x 8 masks (versions 1-8, incl. version info) and for automatic mask choice; unit test pins one reference hash.
- Demo CSVs pass aed-standard/validate.py from main (exit 0); fictional records only.
- Full gate on 92442ce: source verifier, compose config, Django tests (13, OK; run with `-p aed-l7` isolated project instead of the shared stack), copy check, client config: all exit 0.
- Live (isolated stack aed-l7, my branch): GET device 200; versioned /1.4 alias 200 after kwargs fix; POST without consent 400, with consent 201; MailHog emails to the responsible institution's agent and editor only. Real admin logins: demo.editor sees report 1 and not report 2, legionowo editor/agent the reverse; foreign change page redirects to index.
- Browser (Chrome, http://localhost:4217): device page in portal layout; empty submit shows field errors, aria-invalid and an alert; consent checkbox appears with contact; report 2 accepted with focus on the status. 360x800 mobile: no horizontal overflow, all buttons >= 44 px; radio outline raised to #6c757d (4.7:1). Unknown aed_id shows the not-found state. "Najbliższy AED" shows in PoCoTo after `seed_aed_showcase --url`; without the L4 dataset the command stops with a clear error.
- Independent review (separate session, head 36f9cc5): APPROVE, minor 1 (unbounded public POST body), nit 1. Fixed: 16 KB cap with 413; test added after the fix (old code would answer 400, not 413); live 413 for 20 KB, 201 for a normal report. 15 Django tests OK.
- Rebased on main b653dc8 (L4 aggregator #8, Leaflet fix #9): kept both app registrations and gate modules. Showcase now prefers the aggregator's map CSV (`aed-raport-csv`). Live: `aed_refresh` published dataset 6 (74 records), `seed_aed_showcase` without --url linked `/pl/dataset/6,raport-zbiorczy-aed/resource/6,raport-zbiorczy-aed-csv/map`; the map renders 73 points with the location/radius options control. Full gate: 35 Django tests OK (seed + aggregate + reports), other gate commands exit 0.
- Pre-merge update onto main 66f22e6 (L5 wizard #5): union of jury.py app/menu blocks, gate test modules (aggregate, wizard, reports), source-verifier entries and README paragraphs; AGENTS.md pin refreshed. Full gate: source verifier, compose config, 56 Django tests OK, copy check, client config, all exit 0.
