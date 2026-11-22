# Rejestr urządzeń z raportu zbiorczego i formularz bez danych osobowych
Issue: APP-60
Run: efd86b2a-449d-40f2-8518-10fe9f52d8ea
Source doc: .ai/specs/2026-11-22-aed-report-devices.md
Route: agreed delivery (juror round 2, coordinator decision)

## Progress
1. [x] Testy RED; komenda load_aed_report_devices (GREEN).
2. [x] Imię opcjonalne: API, formularz, klauzula, e-mail, testy.
3. [ ] Na żywo i w przeglądarce; pełny gate, review, PR, merge.

## Evidence
- RED: with a stub `sync_report_rows` and the old required name, 6 tests failed for the expected reasons (`Unknown command: 'load_aed_report_devices'`, sync counts `(0, 0) != (1, 2)`, `reporter_name` "To pole jest obowiązkowe."). Two existing tests were changed to the new decision (name no longer reported as an error; form valid without a name).
- GREEN: 22 aed_reports tests OK, including an end-to-end test (seed_jury + aed refresh(process=False) + `load_aed_report_devices`, rerun idempotent, report routed to the device's institution); pyflakes clean; `makemigrations --check`: no changes. `load_aed_devices` now shares the row parser `device_fields`.
- Live (isolated stack with the published report): first run `74 rows, 74 new, 0 without dysponent, 0 held by another institution, 0 invalid`; second run `0 new, 74 updated`. Devices by institution: jury-krosno 21, jury-legionowo 26 (24 report + 2 demo), jury-marki 8, jury-przemysl 21, jury-demo 3 (demo).
- Live report on a Krosno report device without name or contact: 201; QR 200; MailHog email only to krosno.agent and krosno.editor, name shown as "nie podano"; real admin logins: krosno.editor sees it, legionowo.editor does not (change page redirects).
- Browser: report-backed device page (/pl/aed/cf598488-...) renders, label "Imię lub podpis (opcjonalnie)", report without personal data accepted ("Zgłoszenie nr 5 ... Krosno"); axe-core 4.10.2 on `main`: 0 violations before and after submit.
- Full gate: source verifier, compose config, 67 Django tests OK, copy check, client config: all exit 0.
- Review (separate session, head a770b34): APPROVE, minor 2. Fixed: (1) a record merged from an official dataset of one institution and a dysponent publication of another went to the first source; `dysponent:` now wins (test RED `Marki != Demo`, then GREEN); (2) the "nie podano" email assertion ran over an empty outbox; the test institution now has an email and the test asserts one message. 23 aed_reports tests OK.
- Rebased onto main ee46a96 (#17 brand on the device page): clean, the brand band and the optional name sit in different template hunks. Full gate: source verifier, compose config, 68 Django tests OK, copy check, client config. Browser on the report-backed device page: brand band present, label "Imię lub podpis (opcjonalnie)", axe-core 4.10.2 on `main` 0 violations with the form closed and open.
