# Strona akcji AED z mapą pokrycia gmin
Issue: APP-44

## Problem
Dysponenci AED i jury nie mają w lokalnym portalu dane.gov.pl jednego miejsca, które wyjaśnia akcję, pokazuje, ile danych AED już opublikowano i gdzie są luki, oraz prowadzi dysponenta do publikacji własnych danych.

## Rezultat
Nowa trasa `/pl/aed` w istniejącym układzie `MainLayoutComponent` (nagłówek, stopka i nawigacja portalu bez zmian):

- marka z decyzji koordynatora (2026-11-21): nazwa „Mapa Serc”, slogan „Wszystkie AED pod ręką.”, hasło dla dysponentów „Lista AED w szufladzie nikogo nie uratuje.”, znak wariant 1 (serce z błyskawicą AED jako pinezka, zielony #087F45) ze szkicu `brand-directions/mapa-serc/symbol-1.svg`; wszystko w jednym pliku `aed-campaign.brand.ts`. Po scaleniu finalnych plików L3 w `brand/` znak zostanie podmieniony na finalny;
- odbiorca: zwykły mieszkaniec, prosty język; sekcja dla dysponentów osobno, z CTA;
- liczniki: dysponenci (unikalne `operator_name`), rekordy AED (wiersze raportu), gminy z oficjalnymi danymi z liczby gmin w pliku granic PRG (2479 w wersji GUGiK z 2026-11-10; brief podawał 2477). Gminę rekordu wyznacza 7-cyfrowe `terc` (części gminy miejsko-wiejskiej, typ 4 i 5, liczą się do gminy typu 3), a gdy kod nie wskazuje gminy z PRG - współrzędne;
- mapa pokrycia gmin: gmina z oficjalnym rekordem, gmina, w której tylko OSM zna AED (luka), gmina bez danych; dymek z nazwą gminy, liczbą AED, dysponentami i liczbą punktów OSM;
- tekstowa alternatywa mapy: legenda z opisem słownym i tabela gmin z lukami oraz gmin z danymi;
- CTA „Udostępnij swoje AED” do panelu dostawcy (`https://admin.mcod.local/`, w którym L5 dodaje „Dodaj dane AED”).

## Kontrakt danych (publiczne API portalu, bez wewnętrznych modułów L4)
1. `GET /api/1.4/datasets?q=Raport zbiorczy AED` - zbiór, którego tytuł zawiera „Raport zbiorczy AED” (bez rozróżniania wielkości liter).
2. `GET /api/1.4/datasets/:id/resources` - zasób oficjalny: tytuł bez „OSM”/„OpenStreetMap”, format CSV; zasób OSM: tytuł zawiera „OSM” lub „OpenStreetMap”.
3. `GET /api/1.4/resources/:id/data?per_page=100&page=n` - wiersze; nazwy kolumn z `meta.headers_map`. Kolumny oficjalne: `terc`, `operator_name`, `latitude`, `longitude` (standard `aed-standard/`). OSM: `latitude`/`longitude` (albo `lat`/`lon`); gminę punktu OSM wyznacza strona przez punkt w wielokącie gminy. Okno wyników Elasticsearch portalu wynosi 40000 wierszy.
4. Brak zbioru lub zasobu: strona pokazuje stan „Raport zbiorczy nie jest jeszcze opublikowany” zamiast zer udających dane.

Granice gmin: PRG (GUGiK, dane bez opłat, pobrane 2026-11-21), uproszczone do statycznego GeoJSON w `frontend/src/assets/aed/gminy.geojson` z polami `terc` (JPT_KOD_JE) i `name`. Atrybucja na stronie.

## Zakres
Nowy moduł `frontend/src/app/pages/aed-campaign/`, jedna linia trasy w `app-routing.module.ts`, plik granic w `assets/aed/`, wpis o modyfikacji w `UPSTREAM.md` i `scripts/check-portal-source.py`. Bez nowych zależności: Leaflet jest już zależnością portalu; strona ładuje go przez dynamiczny `import('leaflet')`, bo istniejący `LeafletService` używa `require('leaflet')`, którego obecny serwer deweloperski (esbuild) nie obsługuje. Bez zmian backendu, globalnych stylów, nagłówka, strony głównej i `LeafletService`.

## Poza zakresem
Agregacja (L4), kreator dysponenta (L5), zgłoszenia (L7), finalne pliki logo z `brand/` (podmiana znaku po scaleniu PR L3), tłumaczenie EN.

## Kryteria akceptacji i weryfikacja
1. Obliczenia liczników i klasyfikacji gmin: test jednostkowy Jest (`aed-coverage.spec.ts`), RED przed implementacją, potem GREEN.
2. Trasa `/pl/aed` renderuje się w układzie portalu; nagłówek i stopka bez zmian - przeglądarka, desktop 1280 px i 360 px bez poziomego przewijania.
3. Klawiatura: CTA, mapa i tabela osiągalne Tabem z widocznym fokusem; landmarki, jeden `h1`, kolejność nagłówków, `aria-label` mapy, tekstowa alternatywa - inspekcja drzewa dostępności.
4. Liczby pochodzą z API: obserwacja żądań `/api/1.4/...` w przeglądarce; bez raportu L4 widoczny stan pusty.
5. Nazwa, slogan, hasło dla dysponentów i znak zgodne z decyzją o marce; tekst bez pierwszej osoby liczby mnogiej.
6. `python3 -B scripts/check-portal-source.py` i pełna bramka `validation.commands` przechodzą.

## Ryzyka
- Raport L4 powstaje równolegle; tytuły zasobów i nazwy kolumn mogą się różnić. Kontrakt powyżej zgłaszam koordynatorowi; rozbieżność oznacza drobną poprawkę dopasowania.
- Rozmiar GeoJSON gmin wpływa na czas ładowania: 1,55 MB (0,41 MB gzip) po uproszczeniu mapshaper do 1,2% wierzchołków i dokładności 0,001°. Mapa służy do przeglądu pokrycia, nie do ustalania granic.
- Pobieranie OSM stronami po 100 wierszy przy ~10-15 tys. punktów to ok. 100-150 żądań; równoległość ograniczona do 6.

## Progress
1. [x] Spec, issue APP-44, claim.
2. [x] Granice gmin z PRG: uproszczenie, `terc`, `name`, rozmiar.
3. [x] RED: test obliczeń pokrycia (4 asercje nie przechodzą na zaślepce).
4. [x] GREEN: serwis danych, obliczenia, komponent strony, trasa.
5. [x] Przeglądarka: stan pusty na prawdziwym API; dane przez lokalną atrapę trzech endpointów (rekordy ze scrape gov.pl i Przemyśla, punkty OSM z migawki L4): desktop, 360 px bez przewijania w poziomie, klawiatura z widocznym fokusem. Weryfikacja na prawdziwym raporcie L4 po jego publikacji.
6. [ ] UPSTREAM.md, kontrola źródeł, pełna bramka, PR po scaleniu #3.
