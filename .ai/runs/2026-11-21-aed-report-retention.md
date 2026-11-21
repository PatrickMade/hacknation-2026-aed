# Klauzula RODO i retencja danych zgłaszających AED
Issue: APP-51
Run: d6f7d873-ef27-4695-8e87-67f6d1ecd385
Source doc: .ai/specs/2026-11-21-aed-report-retention.md
Route: agreed delivery (owner decision relayed by the coordinator)

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] Test RED, pola, migracja, logika statusu, usuwanie, komenda, zadanie Celery (GREEN).
2. [x] Klauzula w UI i README; przeglądarka.
3. [ ] Pełny gate, review, PR, merge.

## Evidence
- RED: with a stub `purge_reporter_data`, 3 of 4 retention tests errored on the missing `resolved_at` (KeyError/AttributeError); the reporter-name requirement test passed (characterization).
- GREEN: 17 aed_reports tests OK; migration 0002 adds `resolved_at`, `personal_data_removed_at`, `reporter_name` blank and backfills `resolved_at` from `modified` for already resolved reports; `makemigrations --check`: no changes; pyflakes clean.
- Live (isolated stack): `migrate aed_reports` applied 0002; `purge_aed_reporter_data` ran (0 cleaned, no old resolved reports); browser shows the new clause with the legal-review note on /pl/aed/<demo id>.
- Full gate: source verifier, compose config, 60 Django tests OK (seed, aggregate, wizard, reports), copy check, client config: all exit 0.
- Review (separate session, head 735a9a5): APPROVE, minor 1 fixed in the next commit (removal applies to portal data; the email copy follows the dysponent's rules).
- Pre-merge update onto main f34c19e (L3 #10, L6 #6): clean rebase. Full gate: source verifier, compose config, 60 Django tests OK, copy check, client config; `makemigrations --check`: no changes.
