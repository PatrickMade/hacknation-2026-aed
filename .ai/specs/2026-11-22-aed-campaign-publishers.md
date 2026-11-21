# Wydawcy danych i dysponenci na stronie Mapa Serc
Issue: APP-59
Rozszerza: `.ai/specs/2026-11-21-aed-campaign-page.md` (APP-44)

## Problem
Zmiana zgodności L4 (APP-57, gałąź `feat/aed-compliance`) zmienia kontrakt „Raport zbiorczy AED”:
- urząd miasta, który opublikował dane, trafia do `source_records[].publisher_name` (JSON w komórce CSV);
- `operator_name` rekordów miejskich to instytucja wskazana w polu lokalizacji źródła (flaga `operator_from_location`); kilku dysponentów demonstracyjnych (oznaczonych jako dane demonstracyjne) publikuje przez kreator;
- CSV dostaje 7-cyfrową kolumnę `terc` wyliczoną z granic PRG;
- OSM trafia do osobnego zbioru z licencją ODbL.

Strona `/pl/aed` liczy dziś jedynie unikalne `operator_name` i szuka OSM tylko w zbiorze raportu.

## Rezultat (decyzja koordynatora; pierwotna opcja B zmieniona przez Patryka i mentora)
- Licznik „Dysponenci AED”: unikalne `operator_name` (puste i ewentualne „nieustalony…” pomijane).
- Drugi licznik „Wydawcy danych o AED”: unikalne `publisher_name` ze wszystkich `source_records` rekordów oficjalnych.
- Krótkie wyjaśnienie różnicy: wydawca opublikował zbiór, dysponent odpowiada za urządzenie.
- Tabela gmin z danymi: kolumna „Dysponenci” (do 3 nazw i „i jeszcze N”, bo gmina może mieć dziesiątki dysponentów); dymek mapy: dysponenci i wydawcy danych (po 5).
- Pokrycie gmin: `terc` (gdy wskazuje gminę z PRG), inaczej współrzędne.
- OSM: najpierw zasób OSM w zbiorze raportu; gdy go tam nie ma, zbiór, którego tytuł (bez znaczników `<mark>`) zawiera „OpenStreetMap” i „AED”, i jego zasób CSV.

## Zakres
`frontend/src/app/pages/aed-campaign/` (obliczenia, serwis, komponent, testy) i ten spec. Bez zmian backendu, tras, `UPSTREAM.md` i kontroli źródeł.

## Kryteria akceptacji i weryfikacja
1. Test Jest (RED, potem GREEN): licznik wydawców i dysponentów; wydawcy i dysponenci per gmina; puste i „nieustalony…” nie liczą się jako dysponent.
2. Test Jest serwisu (RED, potem GREEN): `publisher_name` z `source_records`; OSM znaleziony w osobnym zbiorze.
3. Przeglądarka: axe 0 naruszeń na `/pl/aed`, 360 px bez przewijania w poziomie, klawiatura.
4. Sprawdzenie na danych L4 po `aed_refresh` (stos tylko do odczytu) po publikacji PR L4.
5. Pełna bramka `validation.commands` i wymagane CI.

## Ryzyka
- Tytuł nowego zbioru OSM nie jest jeszcze ustalony; dopasowanie po „OpenStreetMap” i „AED” w tytule.
- Dokładne pola L4 potwierdzi bezpośrednio; gałąź L4 nie ma jeszcze commitów; PR bazuje na `main` i przechodzi na `feat/aed-compliance`/`main` po scaleniu PR L4. Kolejność scalania: zaraz po PR L4.

## Progress
1. [x] Issue APP-59, claim, spec.
2. [x] RED: testy liczników, wydawców i wyszukiwania OSM (2 asercje nie przechodzą na zaślepce).
3. [x] GREEN: obliczenia, serwis, komponent, teksty; korekta po zmianie decyzji (dysponenci z `operator_name`).
4. [x] Przeglądarka (atrapa z nowym kontraktem, OSM w osobnym zbiorze): axe-core 4.10.2 0 naruszeń (WCAG 2.x A/AA) na desktopie i 360 px, 360 px bez przewijania w poziomie, 10 elementów fokusowalnych z widocznym fokusem.
5. [ ] Sprawdzenie na danych L4 po scaleniu jego PR; rebase na main.
6. [ ] Pełna bramka, PR, niezależny review, CI, merge gate.
