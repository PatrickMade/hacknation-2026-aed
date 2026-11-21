# Lokalny portal
Issue: APP-42
Source doc: .ai/specs/2026-11-21-portal-local-stack.md
Route: agreed delivery
Evidence: zakres oficjalnego portalu, seedowania i zastąpienia Flutter został określony w zadaniu.

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] Oficjalne źródła, GPLv3, Compose, lokalne ustawienia i telemetria.
2. [x] Test RED/GREEN seeda: 15 kont, 6 instytucji, ponowienie i uprawnienia.
3. [x] Zatrzymanie stacka badawczego, start własnego i sprawdzenie web/API/admin/CMS.
4. [ ] Usunięcie Flutter, dokumentacja, pełny gate, niezależny review i merge.

## Evidence
- Source hashes match the official release archives; source verifier checks 7462 files and 4 documented changed upstream files.
- Compose build, dependency startup, migrate, collectstatic, seed and search_index exited 0. Search indexed 6 institutions. Research services were stopped with volumes preserved.
- RED: Django test runner exited 1, `0 != 15` and `CommandError not raised` against the empty command. GREEN and full gate: 2 integration tests passed, including all 15 logins, idempotency, missing password and organization access.
- Live HTTP: public shell, API/proxy institutions, admin/CMS login forms returned 200. Actual superadmin, Krosno agent and CMS admin logins succeeded.
- Browser: homepage count 6, institutions page lists all six; local flags 202/200; no production telemetry in observed requests. Empty CMS responses remain 404 as documented. Screenshot export unavailable because the browser tool rejected the workspace path; DOM/network evidence was inspected.
- Full validation.commands passed in order on this source candidate. Upstream whitespace remains byte-identical; own-file whitespace check passed.
- Local secret scan: 22 generated env values, no match in staged source. Gitleaks staged scan reported 161 inherited findings: 25 in byte-identical upstream examples/test certificates/library sources and 136 integrity-hash false positives in the manifest; no finding in modified/new application code. Generated local values had no staged match. Celery inspect ping returned pong (1 worker).
