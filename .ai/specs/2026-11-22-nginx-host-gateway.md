# host.docker.internal dla nginx na Dockerze w Linuksie
Issue: APP-71

## Problem i obecny stan
`backend/docker/nginx/config-templates/03-admin.conf.template` kieruje trzy lokalizacje `/media` do `host.docker.internal:8001`. Docker Desktop zapewnia tę nazwę, a zwykły Docker w Linuksie nie. Tam nginx nie przechodzi kontroli konfiguracji przy starcie (`host not found in upstream "host.docker.internal"`), a od PR #31 restartuje się w pętli. Jury może uruchamiać stack na Linuksie.

Przeszukanie `compose.yaml`, szablonów nginx i pozostałych plików repozytorium: nazwę rozwiązuje w działającym stacku tylko ten szablon nginx. Wartości `MCOD_NGINX_*` z `host.docker.internal` w `.env.example` nadpisuje blok `environment` usługi nginx w `compose.yaml`; `backend/docker-compose.yml` i `backend/env.sample` to nieużywane pliki upstream.

## Zmiana
Usługa nginx w `compose.yaml` dostaje `extra_hosts: ['host.docker.internal:host-gateway']` (Docker Engine 20.10 lub nowszy; działa też w Docker Desktop). Szablony nginx upstream bez zmian.

## Kryteria akceptacji i weryfikacja
1. `docker compose --profile tools config --quiet` przechodzi; rozwinięta konfiguracja nginx zawiera `host.docker.internal=host-gateway`.
2. Docker w Linuksie (Engine 29.10): `nginx -t` dla konfiguracji z `proxy_pass http://host.docker.internal:8001` na obrazie bazowym naszego nginx kończy się błędem `host not found in upstream` bez mapowania i sukcesem z nim. Pełnego startu z README na Linuksie nie wykonano (budowa obrazów nie mieści się w czasie zadania).
3. Docker Desktop: jeden start polecenia z README: `up` kod 0, nginx działa, `curl -f localhost:4200/api/1.4/institutions` zwraca 200.
4. Pełna bramka `validation.commands`, niezależny review, merge przez `merge_gate.py`.

## Poza zakresem
Szablony nginx upstream, publikowanie portu panelu na hoście (trasy `/media` przez `host.docker.internal:8001` nadal wymagają usługi na porcie 8001 hosta; to zachowanie upstream).
