# Oficjalne źródła dane.gov.pl

Kod portalu pochodzi z https://dane.gov.pl/source-code/ (pobrano 2026-11-21):

| Katalog | Oficjalne archiwum | SHA-256 |
|---|---|---|
| backend/ | backend_2.62.3.zip | 98b9855d7b47cb8fd8680ab70c6114f138ac46123ea1541fbce2664866f09578 |
| frontend/ | frontend_3.5.2.zip | 6beefede7ccb585fb8229c235d787f358a7de79552b5138dad0f630ec0684a5f |

Archiwa są wersjonowane; nie korzystamy z aliasów latest. `local/upstream-files.json` zawiera SHA-256 każdego pliku w oryginalnych archiwach. `python3 scripts/check-portal-source.py` sprawdza zachowanie źródeł i zamkniętą listę modyfikacji.

Oficjalny plik README.txt jest zachowany jako NOTICE.upstream.txt, a LICENCE.txt jako LICENSE (GNU GPL v3.0). Zgodnie z oficjalną dystrybucją zmodyfikowany portal udostępniamy na GPLv3, zachowując notices i licencje zależności. Frontend zawiera pole MIT w package.json; zachowujemy tę metadaną, ale nie interpretujemy jej jako zmiany oficjalnych warunków dystrybucji całego portalu. Przekazując obrazy lub kod wynikowy, należy przekazać także odpowiadający im kod źródłowy, pliki budowy i licencję. Ten projekt nie jest produkcyjną instancją dane.gov.pl ani oficjalnym serwisem administracji.

## Nasze modyfikacje (2026-11-21)

- backend/docker/app/Dockerfile: utworzenie logs przed kompilacją tłumaczeń (logger wymaga katalogu).
- backend/mcod/settings/jury.py: nowa konfiguracja oparta na local.py.sample; poprawione ustawienia indeksów Elasticsearch (bez index.timeout), lokalne flagi, wyłączona telemetria.
- backend/mcod/core/management/commands/seed_jury.py oraz backend/mcod/core/tests/test_jury_seed.py: powtarzalny seed kont i instytucji oraz testy jego kontraktu.
- backend/mcod/urls.py: jedna linia dołączająca adresy /aed/ kreatora dysponenta AED i publicznego walidatora (APP-43). Kod kreatora jest w nowym katalogu backend/mcod/aed_wizard/, rejestracja aplikacji i pozycja menu w backend/mcod/settings/jury.py, a Compose montuje aed-standard/ tylko do odczytu.
- frontend/proxy.local.conf.json: lokalny serwer flag zamiast produkcyjnego.
- frontend/src/app/app.config.ts: lokalne adresy flag, puste identyfikatory telemetrii.
- frontend/src/app/app.module.ts: wyłączenie Sentry i Matomo.
- backend/mcod/aed_aggregate/ (nowa aplikacja), backend/data/aed/ (datowane kopie źródeł AED) i jedna linia INSTALLED_APPS w backend/mcod/settings/jury.py: raport zbiorczy AED (APP-46). Pliki upstream bez zmian. Dane w backend/data/aed/sources/ mają licencje swoich źródeł, nie GPL v3.0 (backend/data/aed/sources/LICENSES.md).
- frontend/src/app/services/leflet.service.ts (poprawka działania, 2026-11-21): statyczny import ESM `leaflet` zamiast `require('leaflet')`, którego builder esbuild nie obsługuje w przeglądarce; bez tej zmiany zakładka Mapa zasobu i mapa regionów są puste. Bez zmian wyglądu.
- Pliki w katalogu głównym, local/ i scripts/: Compose, konfiguracja lokalna, generowanie env, instrukcja startu, kontrola źródeł i testy. Dotychczasowy szkielet Flutter zostaje zastąpiony portalem.

Nie zmieniamy szablonów, stylów, treści ani layoutu portalu. Pusta baza po migracjach nie zawiera produkcyjnych stron CMS. Seed nie ładuje upstream basic_data.json ani jego kont z publicznie znanymi hasłami.

## Kontrola sekretów w źródłach upstream

.gitleaksignore wskazuje konkretne wystąpienia w niezmienionych archiwach: publiczne przykłady kluczy, certyfikaty testowe, literały w testach oraz fałszywe trafienia w kodzie bibliotek. Nie obejmuje katalogów jako całości. Kontrola SHA-256 każdego z tych plików pozostaje częścią wymaganej bramki. Nowe hasła jury są generowane w .env i nie są objęte wyjątkami.
