# Misja AED - Dane na ratunek

Prototyp konkursowy HackNation 2026 dla zadania Ministerstwa Cyfryzacji. Repozytorium zawiera oficjalny portal dane.gov.pl: backend 2.62.3 (Django/Falcon) oraz frontend 3.5.2 (Angular). Jury uruchamia portal lokalnie. Nie jest to produkcyjna instancja dane.gov.pl.

Ta wersja dostarcza portal i konta demonstracyjne. Funkcje, dane i identyfikacja kampanii AED są rozwijane osobno. Nie zawiera kopii produkcyjnej bazy ani treści CMS. Brak zawartości strony głównej CMS może powodować odpowiedź 404 jej endpointu; lista instytucji i panel administracyjny korzystają z lokalnej bazy.

## Wymagania

Docker z Docker Compose v2 lub nowszym oraz Python 3 do utworzenia lokalnego pliku env. Budowa pobiera zależności z Internetu. Na Apple Silicon obrazy aplikacji, Elasticsearch i MailHog wymagają emulacji linux/amd64. Badawcza budowa zajmowała około 10,5 GB sumarycznych rozmiarów obrazów (ze współdzielonymi warstwami); cache budowy i dane wymagają dodatkowego miejsca. Pierwszy start i migracje mogą potrwać kilka minut.

Porty 80, 443, 4200 i 8025 muszą być wolne. Usługi są wystawione wyłącznie na 127.0.0.1. Stack jest przeznaczony do demonstracji lokalnej, nie do publicznego wdrożenia.

## Uruchomienie od zera

W katalogu głównym repozytorium:

```sh
# Tylko przy pierwszym uruchomieniu. Nie nadpisuje istniejącego .env.
python3 scripts/init-env.py

# Jedna konfiguracja Compose dla całego portalu.
docker compose --profile tools --parallel 1 build manage frontend db elasticsearch redis rabbitmq rdfdb nginx
docker compose up -d --wait db elasticsearch redis rabbitmq rdfdb smtp flags
docker compose run --rm manage python manage.py migrate --noinput
docker compose run --rm manage python manage.py seed_jury
docker compose run --rm manage python manage.py collectstatic --noinput
docker compose run --rm manage python manage.py search_index --rebuild -f
docker compose run --rm manage python manage.py aed_refresh
docker compose up -d admin api cms celery frontend nginx
```

Generator tworzy `.env` z losowymi hasłami i kluczami, z uprawnieniami 0600. Można zamiast tego skopiować `.env.example` do `.env` i samodzielnie wypełnić puste wartości. `.env` jest ignorowany przez Git i nie trafia do kontekstu budowy. Nie publikuj jego zawartości. Nie używaj haseł ani kluczy z rzeczywistych kont. Hasła odczytaj lokalnie z `.env` w edytorze.

Seed wymaga wszystkich 15 haseł przed zapisem. Można go uruchamiać ponownie: zachowuje identyfikatory kont i instytucji, ustawia hasła zgodnie z `.env` oraz odtwarza przypisania kont demo. Nie uruchamiaj go na bazie produkcyjnej. Nie ładuje kont ani przykładowego zbioru z upstream `basic_data.json`.

`aed_refresh` (po `seed_jury`) wczytuje datowane kopie pięciu zbiorów AED z dane.gov.pl (`backend/data/aed/sources/`) jako zbiory instytucji demo, mapuje je do wzorcowego zakresu `aed-standard/`, waliduje i deduplikuje, a potem publikuje zbiór „Raport zbiorczy AED” instytucji operatora portalu: CSV z podglądem mapy, GeoJSON oraz osobny zasób punktów AED z OpenStreetMap na licencji ODbL 1.0. Polecenie można uruchamiać ponownie; zmienione pliki zastępują poprzednie wersje tych samych zasobów. Tę samą aktualizację wykonuje zadanie Celery `mcod.aed_aggregate.tasks.aed_refresh_task` (harmonogram dzienny wymaga procesu celery beat, którego lokalny Compose nie uruchamia).

Frontend kompiluje się po starcie kontenera. Postęp: `docker compose logs -f frontend`. Gotowość sprawdzisz przez `curl -f http://localhost:4200/` oraz `curl -f http://localhost:4200/api/1.4/institutions`.

## Lokalne nazwy i certyfikat

Dodaj do systemowego pliku hosts (na Linux/macOS `/etc/hosts`, na Windows `C:\Windows\System32\drivers\etc\hosts`) wpis:

```text
127.0.0.1 mcod.local api.mcod.local admin.mcod.local cms.mcod.local mail.mcod.local
```

Zmiana wymaga uprawnień administratora systemu. Przeglądarka musi zaakceptować dostarczony upstream lokalny certyfikat dla nazw `*.mcod.local`. Przy pierwszym otwarciu każdego hosta zaakceptuj wyjątek certyfikatu tylko dla tej lokalnej instancji. Certyfikaty znajdują się w `backend/docker/nginx/certs/`; nie są certyfikatami produkcyjnymi. Nie wyłączaj globalnie kontroli TLS. Można też zgodnie z polityką własnego systemu dodać lokalny certyfikat do zaufanych; repozytorium nie modyfikuje systemowego magazynu certyfikatów.

| Adres | Zastosowanie |
|---|---|
| http://localhost:4200/ | Publiczny frontend bez konfiguracji hosts |
| https://mcod.local/ | Frontend przez lokalny nginx |
| https://api.mcod.local/doc | Dokumentacja API |
| https://api.mcod.local/1.4/institutions | Instytucje w lokalnym API |
| https://admin.mcod.local/login/ | Panel dostawcy i administratora |
| https://cms.mcod.local/admin/login/ | Panel CMS |
| http://localhost:8025/ | MailHog - lokalny podgląd wiadomości, bez wysyłki na zewnątrz |

Do diagnostyki bez zmiany hosts: `curl -k --resolve api.mcod.local:443:127.0.0.1 https://api.mcod.local/1.4/institutions`. `-k` służy tutaj wyłącznie do sprawdzenia lokalnego certyfikatu.

## Konta demonstracyjne

| Login | Rola | Zmienna hasła w .env |
|---|---|---|
| superadmin@mcod.local | Superadmin tworzony jako pierwszy | SEED_SUPERADMIN_PASSWORD |
| admin@mcod.local | Administrator portalu | SEED_ADMIN_PASSWORD |
| user@mcod.local | Zwykły użytkownik bez dostępu do panelu | SEED_USER_PASSWORD |
| krosno.agent@mcod.local / krosno.editor@mcod.local | Pełnomocnik / edytor Krosna | SEED_KROSNO_AGENT_PASSWORD / SEED_KROSNO_EDITOR_PASSWORD |
| marki.agent@mcod.local / marki.editor@mcod.local | Pełnomocnik / edytor Marek | SEED_MARKI_AGENT_PASSWORD / SEED_MARKI_EDITOR_PASSWORD |
| przemysl.agent@mcod.local / przemysl.editor@mcod.local | Pełnomocnik / edytor Przemyśla | SEED_PRZEMYSL_AGENT_PASSWORD / SEED_PRZEMYSL_EDITOR_PASSWORD |
| warszawa.agent@mcod.local / warszawa.editor@mcod.local | Pełnomocnik / edytor Warszawy | SEED_WARSZAWA_AGENT_PASSWORD / SEED_WARSZAWA_EDITOR_PASSWORD |
| legionowo.agent@mcod.local / legionowo.editor@mcod.local | Pełnomocnik / edytor Legionowa | SEED_LEGIONOWO_AGENT_PASSWORD / SEED_LEGIONOWO_EDITOR_PASSWORD |
| demo.agent@mcod.local / demo.editor@mcod.local | Pełnomocnik / edytor dysponenta demo | SEED_DEMO_AGENT_PASSWORD / SEED_DEMO_EDITOR_PASSWORD |

Portal reprezentuje administratora flagą `is_superuser`; oba konta administracyjne mają tę rolę. Instytucje wskazują superadmina jako twórcę. Pełnomocnicy i edytorzy są przypisani tylko do własnej instytucji. Nazwy profili i numer `000000000` są danymi fikcyjnymi wymaganymi przez panel, nie kontaktami do urzędów.

## Zatrzymanie i kolejne uruchomienie

```sh
docker compose stop
# Powrót do istniejącej, przygotowanej bazy:
docker compose up -d
```

`stop` zachowuje kontenery i dane. `docker compose down` usuwa kontenery i sieć, zachowując nazwane wolumeny. Nie dodawaj `--volumes`, jeśli chcesz zachować bazę, media i indeksy. Nie uruchamiaj równocześnie innej instancji na tych samych portach.

## Kod i sprawdzenia

- `backend/`: oficjalne źródła Django, Falcon, Wagtail i Celery; ustawienia lokalne `mcod/settings/jury.py`; komenda `seed_jury`.
- `frontend/`: oficjalny Angular, lokalny proxy, Sentry i Matomo wyłączone.
- `compose.yaml`: PostgreSQL, Elasticsearch, Redis, RabbitMQ, Fuseki, MailHog, flagi, aplikacje i nginx.
- `local/`, `scripts/`: konfiguracja i sprawdzenie pochodzenia źródeł.
- `backend/mcod/aed_wizard/`: kreator „Dodaj dane AED” w panelu dostawcy (`https://admin.mcod.local/aed/kreator/`, konta pełnomocnika i edytora instytucji) oraz publiczny walidator „Sprawdź swój plik” (`https://admin.mcod.local/aed/sprawdz-plik/`). Reguły zgodności pochodzą z `aed-standard/validate.py`. Testy kreatora są częścią bramki poniżej (`mcod.aed_wizard`).

Po budowie obrazów i przygotowaniu usług/bazy z instrukcji startu uruchom bramkę w tej kolejności:

```sh
python3 -B scripts/check-portal-source.py
docker compose --profile tools config --quiet
docker compose run --rm manage python manage.py test mcod.core.tests.test_jury_seed mcod.aed_aggregate mcod.aed_wizard mcod.aed_reports --noinput --keepdb
python3 -B .ai/scripts/check_project_copy.py
python3 -B .ai/scripts/check_client_config.py
```

Test obejmuje seed, ponowienie, brak hasła, logowanie edytorów i odmowę dostępu do obcej instytucji oraz panelu dla zwykłego użytkownika. Testy `mcod.aed_aggregate` sprawdzają mapowanie źródeł AED do wzorcowego zakresu, deduplikację, pochodzenie rekordów, walidację przez `aed-standard/validate.py` oraz publikację zasobów raportu. Testy `mcod.aed_wizard` sprawdzają mapowanie plików dysponentów do standardu, raport walidacji, publikację przez konto instytucji, publiczny walidator oraz to, że opublikowany zasób trafia do raportu zbiorczego po odświeżeniu. Testy `mcod.aed_reports` sprawdzają moduł zgłoszeń AED: API, zgodę RODO, zakres panelu, e-mail, kod QR i komendy. Nie jest to pełny zestaw testów całego portalu.

## Zgłoszenia AED i kody QR

Moduł `backend/mcod/aed_reports/` prowadzi rejestr urządzeń AED po `aed_id` ze wzorcowego zakresu danych i przyjmuje zgłoszenia problemów do dysponenta. Fikcyjne urządzenia demonstracyjne załadujesz po `seed_jury`:

```sh
docker compose run --rm manage python manage.py load_aed_devices mcod/aed_reports/data/demo-jury-demo.csv --organization jury-demo
docker compose run --rm manage python manage.py load_aed_devices mcod/aed_reports/data/demo-jury-legionowo.csv --organization jury-legionowo
```

Plik każdego dysponenta musi mieć układ standardu i przejść jego walidator; komenda aktualizuje urządzenia po `aed_id` i odrzuca identyfikator należący do innej instytucji.

| Adres | Zastosowanie |
|---|---|
| https://mcod.local/pl/aed/5b0c3c1e-6f0e-4a57-9d4e-2f1a3b7c8d01 | Strona urządzenia demo z przyciskiem „Zgłoś problem” (adres z kodu QR) |
| `https://api.mcod.local/aed/devices/<aed_id>/qr.svg` | Kod QR strony urządzenia do naklejki |
| https://admin.mcod.local/aed_reports/aedincidentreport/ | Zgłoszenia w panelu: tylko konta instytucji odpowiedzialnej za urządzenie, statusy nowe / w trakcie / rozwiązane |
| http://localhost:8025/ | E-mail o nowym zgłoszeniu do adresu instytucji i jej kont |

Wpis „Najbliższy AED” w sekcji PoCoTo wskazuje mapę zasobu zbioru „Raport zbiorczy AED” z filtrem odległości. Uruchom go po opublikowaniu tego zbioru: `docker compose run --rm manage python manage.py seed_aed_showcase` (albo z `--url <adres mapy>`).

Ograniczenia prototypu: strona urządzenia wywołuje API przez lokalny proxy `/api` serwera frontendu (konfiguracja Compose), a nieznany identyfikator pokazuje komunikat na stronie zamiast przekierowania na stronę 404 portalu; brak limitu zgłoszeń z jednego adresu.

Klauzula pod formularzem (wzór do weryfikacji prawnej): administratorem danych zgłaszającego (imię lub podpis, opcjonalny kontakt) jest dysponent urządzenia; operator portalu wyłącznie przekazuje zgłoszenie. Imię i kontakt są usuwane z portalu 30 dni po oznaczeniu zgłoszenia jako „rozwiązane”; treść zgłoszenia zostaje bez danych osobowych. Kopia zgłoszenia wysłana e-mailem do dysponenta podlega jego zasadom przechowywania. Usuwanie wykonuje `docker compose run --rm manage python manage.py purge_aed_reporter_data` oraz dzienne zadanie Celery `mcod.aed_reports.tasks.purge_reporter_data_task` (wymaga procesu celery beat, którego lokalny Compose nie uruchamia). Ponowne otwarcie zgłoszenia liczy 30 dni od nowa.

## Licencja i użycie AI

Portal i nasze modyfikacje są udostępniane na GNU GPL v3.0. Wyjątek: datowane kopie danych źródłowych w `backend/data/aed/sources/` nie są objęte GPL v3.0; zachowują licencje źródeł (CC0 1.0, CC BY 4.0, OpenStreetMap: ODbL 1.0), opisane w `backend/data/aed/sources/LICENSES.md`. Zobacz `LICENSE`, `NOTICE.upstream.txt` i `UPSTREAM.md` z wersjami, sumami archiwów i listą zmian. Zachowano oryginalne notices i licencje zależności.

AI wspierało analizę, konfigurację lokalną, seed kont, agregator raportu zbiorczego AED (mapowanie, deduplikacja, publikacja), kod kreatora AED i walidatora, moduł zgłoszeń AED z koderem QR, testy i dokumentację tej wersji. Oficjalny kod portalu pochodzi z dystrybucji dane.gov.pl. Zakres użycia AI należy aktualizować w materiałach zgłoszenia zgodnie z regulaminem HackNation §2 ust. 8; końcowy rezultat wymaga przeglądu i odpowiedzialności zespołu.
