# Kolejność startu nginx
Issue: APP-70
Source doc: .ai/specs/2026-11-22-nginx-start-order.md
Route: agreed delivery
Evidence: końcowe QA integracyjne odtworzyło wyścig (2 z 3 startów), koordynator określił poprawkę w compose.yaml.

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] RED z compose.yaml z main: 3 świeże starty, w 2 nginx exited (exit 1, `host not found in upstream "frontend"`).
2. [x] depends_on (service_started) na frontend, api, admin, cms, smtp i restart: on-failure; config --quiet exit 0.
3. [x] GREEN: 3 świeże starty polecenia z README: up exit 0, nginx running (0 restartów, 0 linii emerg), curl -f institutions 200 (6 instytucji), https://mcod.local 200.
4. [ ] Pełna bramka, PR, niezależny review, merge przez merge_gate.py.
