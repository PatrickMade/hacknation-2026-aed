# Mapa zasobu w lokalnym portalu: import Leaflet jako ESM
Issue: APP-49

## Problem i obecny stan
W lokalnym portalu (APP-42) zakładka Mapa zasobu jest pusta. Konsola pokazuje `Dynamic require of "leaflet" is not supported` z `frontend/src/app/services/leflet.service.ts:44` (`this.L = require('leaflet')`). Frontend buduje `@angular/build:application` (esbuild), który nie obsługuje CommonJS `require` w kodzie przeglądarki. Ten sam serwis obsługuje mapę regionów na stronie wyszukiwania zbiorów.

## Zmiana
Zastępujemy `require('leaflet')` statycznym importem ESM (`import * as leaflet from 'leaflet'`). Zachowujemy warunek `isPlatformBrowser`. Projekt buduje tylko pakiet przeglądarkowy (brak SSR w `angular.json`), więc import na poziomie modułu nie uruchamia Leaflet po stronie serwera. Nie zmieniamy designu, treści, układu ani stylu mapy. Zmianę zapisujemy w UPSTREAM.md jako poprawkę działania i dopisujemy plik do zamkniętej listy modyfikacji w `scripts/check-portal-source.py`.

## Kryteria akceptacji i weryfikacja
1. Zasób CSV z kolumnami przypisanymi do ról `label`, `b`, `l` pokazuje w zakładce Mapa mapę Leaflet z kafelkami i jednym znacznikiem na wiersz. Przed zmianą: błąd `Dynamic require` w konsoli i brak `app-map`. Scenariusz w przeglądarce na lokalnym stacku.
2. Mapa regionów na `/pl/dataset?isMapOpen=true` renderuje się bez tego błędu.
3. `python3 -B scripts/check-portal-source.py` przechodzi i wymienia 5 udokumentowanych modyfikacji; plik jest opisany w UPSTREAM.md.
4. Pełna bramka `validation.commands` przechodzi; niezależny review; merge przez `merge_gate.py`.

## Poza zakresem
Funkcje i dane AED, wygląd mapy, źródło kafelków (upstream używa tile.openstreetmap.org), inne zmiany upstream. Testowy zbiór do weryfikacji powstaje tylko w lokalnej bazie i nie trafia do repozytorium.
