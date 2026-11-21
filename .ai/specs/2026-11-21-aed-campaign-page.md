# Strona akcji AED z mapą pokrycia gmin
Issue: APP-44

## Problem
Dysponenci AED i jury nie mają w lokalnym portalu dane.gov.pl jednego miejsca, które wyjaśnia akcję, pokazuje, ile danych AED już opublikowano i gdzie są luki, oraz prowadzi dysponenta do publikacji własnych danych.

## Rezultat
Nowa trasa `/pl/aed` w istniejącym układzie `MainLayoutComponent` (nagłówek, stopka i nawigacja portalu bez zmian):

- marka z decyzji koordynatora (2026-11-21): nazwa „Mapa Serc”, slogan „Wszystkie AED pod ręką.”, hasło dla dysponentów „Lista AED w szufladzie nikogo nie uratuje.”, finalny znak L3 (APP-48): pełny kontur Polski z wyciętym sercem AED, plik `brand/logo/mapa-serc-symbol-kolor.svg`, skopiowany bajt w bajt do `frontend/src/assets/aed/` (build Angular serwuje tylko `frontend/src/assets`) i wyświetlany jako obraz dekoracyjny obok `h1`; kolory z `brand/tokens.css` (#087F45, #0B2E20, #DDF3E6). Tekst marki w jednym pliku `aed-campaign.brand.ts`;
- odbiorca: zwykły mieszkaniec, prosty język; sekcja dla dysponentów osobno, z CTA;
- liczniki: dysponenci (unikalne `operator_name`), rekordy AED (wiersze raportu), gminy z oficjalnymi danymi z liczby gmin w pliku granic PRG (2479 w wersji GUGiK z 2026-11-10; brief podawał 2477). Gminę rekordu wyznaczają współrzędne; 7-cyfrowe `terc`, jeśli kiedyś się pojawi, ma pierwszeństwo (części gminy miejsko-wiejskiej, typ 4 i 5, liczą się do gminy typu 3);
- mapa pokrycia gmin: gmina z oficjalnym rekordem, gmina, w której tylko OSM zna AED (luka), gmina bez danych; dymek z nazwą gminy, liczbą AED, dysponentami i liczbą punktów OSM;
- tekstowa alternatywa mapy: legenda z opisem słownym i tabela gmin z lukami oraz gmin z danymi;
- CTA „Udostępnij swoje AED” do panelu dostawcy (`https://admin.mcod.local/`, w którym L5 dodaje „Dodaj dane AED”).

## Kontrakt danych (publiczne API portalu, bez wewnętrznych modułów L4)
1. `GET /api/search?q=Raport zbiorczy AED&model[terms]=dataset&per_page=10` (istniejące `DatasetService.getAll`) - zbiór, którego tytuł zawiera „Raport zbiorczy AED” (bez rozróżniania wielkości liter).
2. `GET /api/1.4/datasets/:id/resources` - zasób oficjalny: tytuł bez „OSM”/„OpenStreetMap”, format CSV; zasób OSM: tytuł zawiera „OSM” lub „OpenStreetMap” (u L4: „Punkty AED z OpenStreetMap - Polska (ODbL 1.0)”); zasób oficjalny u L4: „Raport zbiorczy AED (CSV)”.
3. `GET /api/1.4/resources/:id/data?per_page=100&page=n` - wiersze; nazwy kolumn z `meta.headers_map`. Kolumny oficjalne: `operator_name`, `latitude`, `longitude`; `terc` jest opcjonalne. Zmiana kontraktu od L4 (PR #8, head a36cd828, decyzja koordynatora - opcja A): raport zbiorczy nie ma kolumny `terc`, bo żadne źródło nie ma poprawnego 7-cyfrowego kodu, a standard zabrania zgadywania. Gminę rekordu oficjalnego i punktu OSM wyznacza więc strona ze współrzędnych przez punkt w wielokącie gminy z dołączonych granic PRG; `terc` jest używane tylko wtedy, gdy istnieje i wskazuje gminę z PRG. Rekord bez współrzędnych liczy się do rekordów i dysponentów, ale nie do gmin. OSM: `latitude`/`longitude` (albo `lat`/`lon`). Okno wyników Elasticsearch portalu wynosi 40000 wierszy; gdy zasób ma ich więcej, strona pokazuje komunikat, że liczby mogą być zaniżone. Wartość `terc` z 6 cyframi (liczba bez wiodącego zera) jest uzupełniana do 7 cyfr.
4. Brak zbioru lub zasobu: strona pokazuje stan „Raport zbiorczy nie jest jeszcze opublikowany” zamiast zer udających dane.

Granice gmin: PRG (GUGiK, dane bez opłat, pobrane 2026-11-21), uproszczone do statycznego GeoJSON w `frontend/src/assets/aed/gminy.geojson` z polami `terc` (JPT_KOD_JE) i `name`. Atrybucja na stronie.

## Zakres
Nowy moduł `frontend/src/app/pages/aed-campaign/`, jedna linia trasy w `app-routing.module.ts`, plik granic w `assets/aed/`, wpis o modyfikacji w `UPSTREAM.md` i `scripts/check-portal-source.py`. Bez nowych zależności: Leaflet jest już zależnością portalu; strona ładuje go przez dynamiczny `import('leaflet')`, bo istniejący `LeafletService` używa `require('leaflet')`, którego obecny serwer deweloperski (esbuild) nie obsługuje. Bez zmian backendu, globalnych stylów, nagłówka, strony głównej i `LeafletService`.

## Poza zakresem
Agregacja (L4), kreator dysponenta (L5), zgłoszenia (L7), zmiany plików `brand/` po scaleniu PR L3 (kopię w assets trzeba wtedy odświeżyć), tłumaczenie EN.

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
6. [x] UPSTREAM.md, kontrola źródeł, pełna bramka, PR #6 po scaleniu #3.
7. [x] Poprawki po review: linki wewnątrz strony przewijają do sekcji i przenoszą fokus (portal ma `<base href="/">`), komunikat o limicie 40000 wierszy, `terc` bez wiodącego zera, brak mapy po opuszczeniu strony w trakcie ładowania Leaflet.
8. [x] Zmiana kontraktu L4 (brak `terc`, gminy ze współrzędnych): test charakteryzujący i sprawdzenie na atrapie z tytułami zasobów L4.
9. [x] Finalny znak i kolory z `brand/` (L3).
10. [ ] Niezależny review nowego head, CI, merge gate (kolejność 6).
