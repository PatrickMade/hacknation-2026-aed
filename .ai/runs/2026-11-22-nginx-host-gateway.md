# host.docker.internal dla nginx
Issue: APP-71
Source doc: .ai/specs/2026-11-22-nginx-host-gateway.md
Route: agreed delivery
Evidence: uwaga z review PR #31 i polecenie koordynatora (extra_hosts host-gateway).

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] Przeszukanie użyć `host.docker.internal`: tylko nginx (03-admin.conf.template).
2. [x] `extra_hosts` na nginx; `config --quiet` exit 0, rozwinięta konfiguracja z `host-gateway`.
3. [x] Linux Docker 29.10: `nginx -t` bez mapowania `host not found in upstream "host.docker.internal"`, z mapowaniem sukces (`172.17.0.1 host.docker.internal`); tymczasowy projekt usunięty.
4. [x] Docker Desktop: start z README, up exit 0, curl -f institutions 200, nginx running 0 restartów, https://mcod.local 200.
5. [ ] Pełna bramka, PR, niezależny review, aktualizacja z main po PR #30, merge przez merge_gate.py.
