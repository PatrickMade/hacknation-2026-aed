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
- Licznik „Wydawcy danych o AED”: unikalne `publisher_name` ze wszystkich `source_records` rekordów oficjalnych. Publikacja samego dysponenta (`source_id` zaczyna się od `dysponent:`) nie ma `publisher_name` w danych L4 (`demo.py`, kreator), więc jej wydawcą jest dysponent (`operator_name` rekordu). Na danych L4 z demo: 4 urzędy miast i 4 dysponentów demonstracyjnych.
- Licznik „Potwierdzeni dysponenci AED”: unikalne `operator_name` rekordów z potwierdzonym dysponentem wg reguły L4 (w demo 4); puste i „nieustalony…” pomijane. Brak albo nieczytelne `quality_flags` nie potwierdzają dysponenta (chyba że jest źródło `dysponent:`).
- Krótkie wyjaśnienie: wydawca opublikował zbiór, dysponent odpowiada za urządzenie, a potwierdzony jest wtedy, gdy sam publikuje w portalu dane o swoich urządzeniach (wtedy jest też ich wydawcą).
- Tabela gmin z danymi: kolumna „Wydawcy danych” (do 3 nazw i „i jeszcze N”); dymek mapy: potwierdzeni dysponenci i wydawcy danych (po 5).
- Pokrycie gmin: `terc` (gdy wskazuje gminę z PRG), inaczej współrzędne.
- OSM: najpierw zasób OSM w zbiorze raportu; gdy go tam nie ma, zbiór, którego tytuł (bez znaczników `<mark>`) zawiera „OpenStreetMap” i „AED”, i jego zasób CSV. Błąd wyszukiwania zbioru OSM nie ukrywa liczników z danych oficjalnych: strona pokazuje je i komunikat o błędzie OSM.

## Zakres
`frontend/src/app/pages/aed-campaign/` (obliczenia, serwis, komponent, testy) i ten spec. Bez zmian backendu, tras, `UPSTREAM.md` i kontroli źródeł.

## Kryteria akceptacji i weryfikacja
1. Test Jest (RED, potem GREEN): licznik wydawców i potwierdzonych dysponentów; nazwa z tekstu lokalizacji (`operator_from_location`) nie jest dysponentem; wydawcy i dysponenci per gmina; puste i „nieustalony…” pomijane.
2. Test Jest serwisu (RED, potem GREEN): `publisher_name` z `source_records`, a dla źródła `dysponent:` bez `publisher_name` (kształt L4) wydawcą jest dysponent; potwierdzenie dysponenta z `source_id`/flag, nieczytelne flagi nie potwierdzają; OSM znaleziony w osobnym zbiorze; błąd wyszukiwania OSM zostawia rekordy oficjalne, a komponent pokazuje liczniki i stan błędu OSM.
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
6. [x] Poprawki po review 6008985147 (RED: 4 asercje w lookup/serwisie i 1 w komponencie, potem GREEN): wydawca publikacji dysponenta, błąd OSM bez utraty liczników, nieczytelne flagi, nazwy i tekst.
7. [ ] Pełna bramka, niezależny review, CI, merge gate.
