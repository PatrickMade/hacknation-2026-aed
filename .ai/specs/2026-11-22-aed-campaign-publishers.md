# Wydawcy danych i potwierdzeni dysponenci na stronie Mapa Serc
Issue: APP-59
Rozszerza: `.ai/specs/2026-11-21-aed-campaign-page.md` (APP-44)

## Problem
Zmiana zgodności L4 (APP-57, gałąź `feat/aed-compliance`) zmienia kontrakt „Raport zbiorczy AED”:
- rekordy miejskie mają `operator_name = "nieustalony"` i flagę `operator_unconfirmed`, bo dysponenta żadne źródło nie potwierdza;
- urząd miasta, który opublikował dane, trafia do `source_records[].publisher_name` (JSON w komórce CSV);
- CSV dostaje 7-cyfrową kolumnę `terc` wyliczoną z granic PRG;
- OSM trafia do osobnego zbioru z licencją ODbL.

Strona `/pl/aed` liczy dziś unikalne `operator_name` jako instytucje i pokazuje je w dymku mapy i tabeli. Po zmianie pokazałaby jedną instytucję „nieustalony”, a OSM mogłoby zniknąć z mapy luk.

## Rezultat (decyzja koordynatora, opcja B)
- Licznik „Wydawcy danych”: unikalne `publisher_name` ze wszystkich `source_records` rekordów oficjalnych (dziś 4).
- Licznik „Potwierdzeni dysponenci”: unikalne `operator_name` bez pustych i bez wartości zaczynających się od „nieustalony” (dziś 0; prawdziwych dodaje kreator L5).
- Dymek mapy i tabela gmin z danymi pokazują wydawców danych (`publisher_name`).
- Krótkie wyjaśnienie różnicy: wydawca opublikował dane, dysponent odpowiada za urządzenie i potwierdza to sam.
- Pokrycie gmin: `terc` (istniejąca logika: `terc`, gdy wskazuje gminę z PRG, inaczej współrzędne).
- OSM: najpierw zasób OSM w zbiorze raportu; gdy go tam nie ma, zbiór, którego tytuł (bez znaczników `<mark>`) zawiera „OpenStreetMap” i „AED”, i jego zasób CSV.

## Zakres
`frontend/src/app/pages/aed-campaign/` (obliczenia, serwis, komponent, testy) i ten spec. Bez zmian backendu, tras, `UPSTREAM.md` i kontroli źródeł.

## Kryteria akceptacji i weryfikacja
1. Test Jest (RED, potem GREEN): liczniki wydawców i potwierdzonych dysponentów; „nieustalony” nie jest dysponentem; wydawcy per gmina.
2. Test Jest serwisu (RED, potem GREEN): `publisher_name` z `source_records`; OSM znaleziony w osobnym zbiorze.
3. Przeglądarka: axe 0 naruszeń na `/pl/aed`, 360 px bez przewijania w poziomie, klawiatura.
4. Sprawdzenie na danych L4 po `aed_refresh` (stos tylko do odczytu) po publikacji PR L4.
5. Pełna bramka `validation.commands` i wymagane CI.

## Ryzyka
- Tytuł nowego zbioru OSM nie jest jeszcze ustalony; dopasowanie po „OpenStreetMap” i „AED” w tytule.
- Gałąź L4 nie ma jeszcze commitów; PR bazuje na `main` i przechodzi na `feat/aed-compliance`/`main` po scaleniu PR L4. Kolejność scalania: zaraz po PR L4.

## Progress
1. [x] Issue APP-59, claim, spec.
2. [ ] RED: testy liczników, wydawców i wyszukiwania OSM.
3. [ ] GREEN: obliczenia, serwis, komponent, teksty.
4. [ ] Przeglądarka (atrapa z nowym kontraktem): axe, 360 px, klawiatura.
5. [ ] Sprawdzenie na danych L4 po scaleniu jego PR; rebase na main.
6. [ ] Pełna bramka, PR, niezależny review, CI, merge gate.
