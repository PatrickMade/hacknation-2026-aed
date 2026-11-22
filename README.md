# Mapa Serc - Misja AED: Dane na ratunek

Prototyp konkursowy HackNation 2026 do zadania Ministerstwa Cyfryzacji „Misja AED - Dane na ratunek”, przygotowany przez zespół jednoosobowy. Repozytorium zawiera oficjalny portal dane.gov.pl, czyli backend 2.62.3 (Django/Falcon) i frontend 3.5.2 (Angular), z dodanym mechanizmem zbierania danych o defibrylatorach AED. Jury uruchamia całość lokalnie jedną konfiguracją Docker Compose. Nie jest to produkcyjna instancja dane.gov.pl.

Co zawiera ta wersja:

- **Wzorcowy zakres danych AED** (`aed-standard/`): słownik 43 pól (XLSX), szablon CSV, schemat Table Schema, przykładowy rekord i walidator.
- **Kreator „Dodaj dane AED” i walidator „Sprawdź swój plik”** (`backend/mcod/aed_wizard/`): dysponent w panelu dostawcy wgrywa plik CSV, XLSX lub GeoJSON, przypisuje kolumny do pól standardu, czyta raport walidacji i publikuje zasób. Walidator działa bez logowania i niczego nie zapisuje.
- **Raport zbiorczy AED** (`backend/mcod/aed_aggregate/`): pięć zbiorów AED z dane.gov.pl zmapowanych do standardu, zwalidowanych i zdeduplikowanych. Zasoby: CSV z podglądem na mapie portalu, GeoJSON oraz osobny zasób punktów AED z OpenStreetMap na licencji ODbL 1.0.
- **Zgłoszenia AED i kody QR** (`backend/mcod/aed_reports/`): kod QR przy urządzeniu prowadzi do jego strony z formularzem „Zgłoś problem”. Zgłoszenie trafia do panelu i na adres e-mail właściwego dysponenta.
- **Strona akcji „Mapa Serc”** (`/pl/aed`): liczniki, mapa pokrycia gmin z lukami (gminy, w których OpenStreetMap zna AED, a brak oficjalnych danych) i przejście do kreatora. W zakładce PoCoTo jest wpis „Najbliższy AED”.
- **Znak akcji** (`brand/`): logo, naklejka z kodem QR i księga znaku.

Wygląd, treści i układ portalu poza obszarami AED pozostają bez zmian. Baza startuje bez kopii produkcyjnej i bez treści CMS, więc endpointy stron CMS (np. strony głównej i klauzuli RODO) odpowiadają 404. Lista instytucji, zbiory, API i panel korzystają z lokalnej bazy.

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

### Cache API po `aed_refresh`

API portalu przechowuje odpowiedzi tabel zasobów (`/1.4/resources/<id>/data`, z nich korzysta strona akcji `/pl/aed`) przez 15 minut w Redis. Odpowiedź zapisana, zanim portal skończy indeksowanie, może więc przez 15 minut pokazywać puste dane, np. 0 luk na mapie pokrycia. Po `aed_refresh` i starcie usług poczekaj, aż Celery opróżni kolejki, czyli aż wszystkie wartości w kolumnie `messages` będą równe 0:

```sh
docker compose exec rabbitmq rabbitmqctl list_queues -q name messages
```

Dopiero wtedy otwórz `/pl/aed`. Jeśli strona pokazała już puste dane, wyczyść cache API i odśwież stronę:

```sh
docker compose exec redis sh -c "redis-cli --scan --pattern 'falcon-cache*' | xargs -r redis-cli del"
```

Polecenie usuwa tylko zapisane odpowiedzi API (klucze `falcon-cache`), a nie dane portalu.

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

## Demo w 10 minut

Wymaga uruchomienia z sekcji wyżej, wpisu w pliku hosts i załadowania urządzeń demo z sekcji „Zgłoszenia AED i kody QR” (`load_aed_devices`, `seed_aed_showcase`). Hasła kont są w lokalnym `.env`.

1. **Strona akcji** https://mcod.local/pl/aed: liczniki i mapa pokrycia gmin. Gdy mapa pokazuje 0 luk, zobacz „Cache API po `aed_refresh`”.
2. **Raport zbiorczy**: w portalu Dane, zbiór „Raport zbiorczy AED”. Zasoby CSV, GeoJSON i OSM; zakładka Mapa zasobu CSV pokazuje punkty. Te same rekordy zwraca API `https://api.mcod.local/1.4/resources/<id zasobu CSV>/data`.
3. **Walidator bez logowania** https://admin.mcod.local/aed/sprawdz-plik/: wgraj np. `backend/data/aed/sources/marki/Defibrylator_GminaMiastoMarki_1.csv` i przeczytaj raport zgodności ze standardem.
4. **Kreator dysponenta**: zaloguj się na https://admin.mcod.local/login/ jako `krosno.agent@mcod.local`, wybierz „Dodaj dane AED”, wgraj `backend/data/aed/sources/krosno/Defibrylator_jAmxQcp.csv`, przypisz kolumny, sprawdź raport walidacji i opublikuj. Rekordy trafią do raportu zbiorczego po kolejnym `aed_refresh`.
5. **Zgłoszenie z kodu QR**: otwórz https://mcod.local/pl/aed/5b0c3c1e-6f0e-4a57-9d4e-2f1a3b7c8d01 i wyślij „Zgłoś problem”. Zgłoszenie widzą w panelu (https://admin.mcod.local/aed_reports/aedincidentreport/) konta instytucji „Dysponent demonstracyjny” (`demo.agent@mcod.local`, `demo.editor@mcod.local`) oraz konta administratorów; konta innych instytucji go nie widzą. Wiadomość e-mail jest w MailHog (http://localhost:8025/).
6. **Najbliższy AED**: w portalu PoCoTo, wpis „Najbliższy AED” prowadzi do mapy raportu z filtrem odległości.

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

Test obejmuje seed, ponowienie, brak hasła, czysty wynik pierwszego seeda (bez śladów wyjątków z sygnałów portalu), logowanie edytorów i odmowę dostępu do obcej instytucji oraz panelu dla zwykłego użytkownika. Testy `mcod.aed_aggregate` sprawdzają mapowanie źródeł AED do wzorcowego zakresu, deduplikację, pochodzenie rekordów, walidację przez `aed-standard/validate.py` oraz publikację zasobów raportu. Testy `mcod.aed_wizard` sprawdzają mapowanie plików dysponentów do standardu, raport walidacji, publikację przez konto instytucji, publiczny walidator oraz to, że opublikowany zasób trafia do raportu zbiorczego po odświeżeniu. Testy `mcod.aed_reports` sprawdzają moduł zgłoszeń AED: API, zgodę RODO, zakres panelu, e-mail, kod QR i komendy. Nie jest to pełny zestaw testów całego portalu.

## Zgłoszenia AED i kody QR

Moduł `backend/mcod/aed_reports/` prowadzi rejestr urządzeń AED po `aed_id` ze wzorcowego zakresu danych i przyjmuje zgłoszenia problemów do dysponenta. Fikcyjne urządzenia demonstracyjne załadujesz po `seed_jury`:

```sh
docker compose run --rm manage python manage.py load_aed_devices mcod/aed_reports/data/demo-jury-demo.csv --organization jury-demo
docker compose run --rm manage python manage.py load_aed_devices mcod/aed_reports/data/demo-jury-legionowo.csv --organization jury-legionowo
```

Po `aed_refresh` zarejestruj urządzenia ze wszystkich rekordów opublikowanego „Raportu zbiorczego AED”, aby każdy rekord miał stronę urządzenia, kod QR i ścieżkę zgłoszenia do swojego dysponenta:

```sh
docker compose run --rm manage python manage.py load_aed_report_devices
```

Instytucję odpowiedzialną wskazują źródła rekordu (`source_records`): plik opublikowany kreatorem (`dysponent:<slug>`) ma pierwszeństwo, w drugiej kolejności zbiór źródłowy instytucji demo (`dane:dataset:<id>`). Rekordy bez takiego źródła (np. OSM) są pomijane. Komendę można uruchamiać ponownie.

Plik każdego dysponenta musi mieć układ standardu i przejść jego walidator; komenda aktualizuje urządzenia po `aed_id` i odrzuca identyfikator należący do innej instytucji.

| Adres | Zastosowanie |
|---|---|
| https://mcod.local/pl/aed/5b0c3c1e-6f0e-4a57-9d4e-2f1a3b7c8d01 | Strona urządzenia demo z przyciskiem „Zgłoś problem” (adres z kodu QR) |
| `https://api.mcod.local/aed/devices/<aed_id>/qr.svg` | Kod QR strony urządzenia do naklejki |
| https://admin.mcod.local/aed_reports/aedincidentreport/ | Zgłoszenia w panelu: konta instytucji odpowiedzialnej za urządzenie oraz administratorzy portalu, statusy nowe / w trakcie / rozwiązane |
| http://localhost:8025/ | E-mail o nowym zgłoszeniu do adresu instytucji i jej kont |

Wpis „Najbliższy AED” w sekcji PoCoTo wskazuje mapę zasobu zbioru „Raport zbiorczy AED” z filtrem odległości. Uruchom go po opublikowaniu tego zbioru: `docker compose run --rm manage python manage.py seed_aed_showcase` (albo z `--url <adres mapy>`).

Ograniczenia prototypu: strona urządzenia wywołuje API przez lokalny proxy `/api` serwera frontendu (konfiguracja Compose), a nieznany identyfikator pokazuje komunikat na stronie zamiast przekierowania na stronę 404 portalu; brak limitu zgłoszeń z jednego adresu.

Klauzula pod formularzem (wzór do weryfikacji prawnej): formularz nie wymaga danych osobowych; administratorem danych podanych przez zgłaszającego (opcjonalnie imię lub podpis i kontakt) jest dysponent urządzenia; operator portalu wyłącznie przekazuje zgłoszenie. Imię i kontakt są usuwane z portalu 30 dni po oznaczeniu zgłoszenia jako „rozwiązane”; treść zgłoszenia zostaje bez danych osobowych. Kopia zgłoszenia wysłana e-mailem do dysponenta podlega jego zasadom przechowywania. Usuwanie wykonuje `docker compose run --rm manage python manage.py purge_aed_reporter_data` oraz dzienne zadanie Celery `mcod.aed_reports.tasks.purge_reporter_data_task` (wymaga procesu celery beat, którego lokalny Compose nie uruchamia). Ponowne otwarcie zgłoszenia liczy 30 dni od nowa.

## Licencja i użycie AI

Portal i modyfikacje w tym repozytorium są udostępniane na GNU GPL v3.0. Wyjątek: datowane kopie danych źródłowych w `backend/data/aed/sources/` nie są objęte GPL v3.0; zachowują licencje źródeł (CC0 1.0, CC BY 4.0, OpenStreetMap: ODbL 1.0), opisane w `backend/data/aed/sources/LICENSES.md`. Zobacz `LICENSE`, `NOTICE.upstream.txt` i `UPSTREAM.md` z wersjami, sumami archiwów i listą zmian. Zachowano oryginalne notices i licencje zależności.

AI (Claude Code i Codex) wspierało analizę zadania i research, zbieranie danych (skrypty pobierające wpisy o AED ze stron urzędów i migawki zbiorów z dane.gov.pl), konfigurację lokalną, seed kont, wzorcowy zakres danych AED, agregator raportu zbiorczego AED (mapowanie, deduplikacja, publikacja), kreator AED i walidator, moduł zgłoszeń AED z koderem QR, stronę akcji „Mapa Serc” z mapą pokrycia gmin i wpisem „Najbliższy AED”, nazwę, znak, naklejkę i księgę znaku akcji (`brand/`), testy, kontrolę jakości (przeglądy w osobnych sesjach AI, kontrola dostępności axe-core), dokumentację oraz teksty i prezentację zgłoszenia. Oficjalny kod portalu pochodzi z dystrybucji dane.gov.pl i nie został wygenerowany przez AI. Pełny zakres użycia AI oraz podział na pracę AI i decyzje autora opisuje `submission/oswiadczenie-ai.md` (regulamin HackNation §2 ust. 8). Decyzje i odpowiedzialność za końcowy rezultat należą do autora.
