# Wydawcy danych i dysponenci na stronie Mapa Serc
Issue: APP-59
Rozszerza: `.ai/specs/2026-11-21-aed-campaign-page.md` (APP-44)

## Problem
Zmiana zgodności L4 (APP-57, gałąź `feat/aed-compliance`) zmienia kontrakt „Raport zbiorczy AED” (pola potwierdzone przez L4):
- urząd miasta, który opublikował dane, jest w `source_records[].publisher_name` (JSON w komórce CSV);
- `operator_name` rekordów miejskich to instytucja z tekstu lokalizacji źródła, zawsze z flagą `operator_from_location`; to nie są potwierdzeni dysponenci;
- dysponenci potwierdzeni to rekordy ze źródłem `source_records[].source_id` zaczynającym się od `dysponent:` (publikacja przez kreator) albo bez flag `operator_from_location` i `operator_unconfirmed`; `seed_aed_demo` publikuje 4 fikcyjnych dysponentów oznaczonych „(dane demonstracyjne)”;
- CSV ma 7-cyfrową kolumnę `terc` z dokładnych granic PRG (73 z 74 rekordów miejskich);
- OSM trafia do osobnego zbioru „Punkty AED z OpenStreetMap - Polska (ODbL 1.0)” (ext_ident `aed-osm-polska`), zasób `aed-osm-csv`, kolumny `latitude`/`longitude` bez zmian.

Strona `/pl/aed` liczy dziś unikalne `operator_name` jako instytucje i szuka OSM tylko w zbiorze raportu.

## Rezultat
Decyzje: koordynator (opcja B), zmiana Patryka i mentora (bez „nieustalony”), definicja pól od L4.
- Licznik „Wydawcy danych o AED”: unikalne `publisher_name` ze wszystkich `source_records` rekordów oficjalnych (dziś 4).
- Licznik „Potwierdzeni dysponenci AED”: unikalne `operator_name` rekordów z potwierdzonym dysponentem wg reguły L4 (w demo 4); puste i „nieustalony…” pomijane.
- Krótkie wyjaśnienie: wydawca opublikował zbiór, dysponent odpowiada za urządzenie, a potwierdzony jest wtedy, gdy sam udostępnia dane w panelu dostawcy.
- Tabela gmin z danymi: kolumna „Wydawcy danych” (do 3 nazw i „i jeszcze N”); dymek mapy: potwierdzeni dysponenci i wydawcy danych (po 5).
- Pokrycie gmin: `terc` (gdy wskazuje gminę z PRG), inaczej współrzędne.
- OSM: najpierw zasób OSM w zbiorze raportu; gdy go tam nie ma, zbiór, którego tytuł (bez znaczników `<mark>`) zawiera „OpenStreetMap” i „AED”, i jego zasób CSV.

## Zakres
`frontend/src/app/pages/aed-campaign/` (obliczenia, serwis, komponent, testy) i ten spec. Bez zmian backendu, tras, `UPSTREAM.md` i kontroli źródeł.

## Kryteria akceptacji i weryfikacja
1. Test Jest (RED, potem GREEN): licznik wydawców i potwierdzonych dysponentów; nazwa z tekstu lokalizacji (`operator_from_location`) nie jest dysponentem; wydawcy i dysponenci per gmina; puste i „nieustalony…” pomijane.
2. Test Jest serwisu (RED, potem GREEN): `publisher_name` z `source_records`; potwierdzenie dysponenta z `source_id`/flag; OSM znaleziony w osobnym zbiorze.
3. Przeglądarka: axe 0 naruszeń na `/pl/aed`, 360 px bez przewijania w poziomie, klawiatura.
4. Sprawdzenie na danych L4 po `aed_refresh` (stos tylko do odczytu) po publikacji PR L4.
5. Pełna bramka `validation.commands` i wymagane CI.

## Ryzyka
- Gałąź L4 ma na razie tylko część `aed-standard` (45433fe); commit agregatora ma przyjść; PR bazuje na `main` i przechodzi na `feat/aed-compliance`/`main` po scaleniu PR L4. Kolejność scalania: zaraz po PR L4.

## Progress
1. [x] Issue APP-59, claim, spec.
2. [x] RED: testy liczników, wydawców i wyszukiwania OSM (2 asercje nie przechodzą na zaślepce).
3. [x] GREEN: obliczenia, serwis, komponent, teksty; korekty po zmianie decyzji i po kontrakcie pól od L4 (RED: 2 asercje, potem GREEN).
4. [x] Przeglądarka (atrapa z polami L4: flagi `operator_from_location`, 4 dysponentów demonstracyjnych `dysponent:`, OSM w osobnym zbiorze; liczniki 7 / 4 / 170 / 6 z 2479): axe-core 4.10.2 0 naruszeń (WCAG 2.x A/AA) na desktopie i 360 px, 360 px bez przewijania w poziomie, 10 elementów fokusowalnych z widocznym fokusem.
5. [ ] Sprawdzenie na danych L4 po scaleniu jego PR; rebase na main.
6. [ ] Pełna bramka, PR, niezależny review, CI, merge gate.
