# Kolejność startu nginx w lokalnym stacku
Issue: APP-70

## Problem i obecny stan
Polecenie z README `docker compose up -d admin api cms celery aed-beat frontend nginx` kończy się kodem 0, ale nginx po około sekundzie kończy działanie z kodem 1: `host not found in upstream ...`. nginx rozwiązuje nazwy wszystkich upstreamów (frontend, api, admin, cms, smtp) raz przy starcie, a w `compose.yaml` nie ma `depends_on` ani polityki restartu, więc może wystartować przed kontenerami, do których kieruje ruch. Końcowe QA integracyjne trafiło to w 2 z 3 świeżych startów; potem https://mcod.local nie działa, a sprawdzenie gotowości z README `curl -f localhost:4200/api/1.4/institutions` zwraca 500.

## Zmiana
W `compose.yaml` usługa nginx dostaje `depends_on` z warunkiem `service_started` na frontend, api, admin, cms i smtp (żadna z nich nie ma healthchecka) oraz `restart: on-failure`, aby przegrany wyścig nazw sam się naprawiał. README i szablony nginx upstream bez zmian.

## Kryteria akceptacji i weryfikacja
1. `docker compose --profile tools config --quiet` przechodzi.
2. RED: z `compose.yaml` z `main` co najmniej jeden z kilku świeżych startów kończy się zatrzymanym nginx (`host not found in upstream`).
3. GREEN: 3 świeże starty polecenia z README na jednym lokalnym projekcie Compose: `up` kod 0, nginx działa, `curl -f localhost:4200/api/1.4/institutions` zwraca 200 za każdym razem.
4. Pełna bramka `validation.commands`, niezależny review, merge przez `merge_gate.py`.

## Poza zakresem
Szablony nginx upstream, inne usługi, kroki README.
