# Odświeżenie prezentacji Mapa Serc po zmianach produktu (PR #24-#27)

Issue: APP-67
Source doc: .ai/specs/2026-11-22-deck-refresh.md
Route: agreed delivery (small change, docs only)
Extends: .ai/specs/2026-11-21-deck-v2.md

## Problem

Prezentacja scalona w PR #16 pokazuje ekrany sprzed zmian produktu, które
weszły do `main` po niej: strona akcji pokazuje dane demonstracyjne osobno
i używa znaku z hasłem (PR #24), kreator nie przypisuje dysponenta do
instytucji wgrywającej plik (PR #26), naklejka ma wiersz o numerze 112
i pole na adres, a znak ma wersję małą (PR #27). Jury po uruchomieniu
portalu zobaczy inne ekrany niż na slajdach. Jurorzy z rundy 3 wskazali
też brak widoku na telefonie i brak zrzutu "Najbliższy AED".

## Outcome

- Slajdy pokazują ekrany lokalnej instancji zbudowanej z `main` 8a83333:
  stronę akcji, kreator, naklejkę i mały symbol; liczby na slajdach
  zgadzają się z tą instancją.
- Jeden nowy slajd "na telefonie" (360 px): strona akcji, karta urządzenia
  i filtr odległości na mapie portalu ("Najbliższy AED"). Podpis mówi, że
  wyszukanie adresu korzysta z publicznego geokodera wbudowanego w portal
  i wymaga internetu. Numeracja slajdów rośnie o jeden.
- `submission/ograniczenia.md` wymienia sprawy, których prototyp nie
  rozwiązuje: identyfikatory zasobów źródłowych wpisane w kod odświeżania,
  zadanie okresowe ograniczone do środowiska lokalnego, brak odświeżania
  punktów OSM, zgodność ze standardem oznaczona słowem kluczowym zamiast
  `dct:conformsTo`, oznaczenie zgodności możliwe przy polach "unknown",
  geokoder wymagający internetu.
- `submission/akceptacja.md` krok 1.4 opisuje wpisanie dysponenta;
  pozostałe teksty w `submission/` zgadzają się ze slajdami.
- `README.md`: raport ma zasoby CSV i GeoJSON, a punkty OSM są osobnym
  zbiorem.

Non-goals: kolejna runda jurorów; czas trwania nagrania (zostaje
1 min 42 s do scalenia PR #23, potem osobna mała zmiana); kod portalu
i pliki marki; zdjęcie znaczników "[do wykonania]" z oświadczenia AI
(czekają na akceptację autora).

## Acceptance

1. `python3 -B submission/prezentacja/build-pdf.py` kończy się kodem 0;
   PDF ma co najmniej 5 stron i najwyżej 10 MB.
2. Kontrola układu (skrypt przeglądarki): żaden obraz nie jest przycięty ani
   zniekształcony, nic nie wychodzi poza slajd ani na przypisy, tytuły mają
   najwyżej 3 wiersze (okładka: 4).
3. Każdy zrzut ekranu pochodzi z instancji zbudowanej z `main` 8a83333
   albo pokazuje ekran, którego PR #24-#27 nie zmieniły.
4. Liczby na slajdach i w tekstach zgadzają się z tą instancją
   i z plikami repozytorium (`aed-standard/schema.json`, `brand/`).
5. Nowe pozycje w `ograniczenia.md` zgadzają się z kodem
   (`backend/mcod/aed_aggregate/sources.py`, `tasks.py`).
6. Brak form 1. osoby liczby mnogiej; brak prywatnych ścieżek,
   identyfikatorów sesji i haseł.
7. Bramka `validation.commands` przechodzi.

## Verification

- `build-pdf.py`, skrypt kontroli układu, przegląd wszystkich stron.
- Porównanie liczb z plikiem CSV raportu i stroną akcji lokalnej instancji.
- grep form liczby mnogiej i wzorców prywatnych danych.
- QA: zmiana tylko dokumentacji, `skip-qa`.

## Progress

1. [x] Issue APP-67 i claim.
2. [ ] Zrzuty z instancji zbudowanej z `main` 8a83333.
3. [ ] Slajdy, slajd mobilny, kontrola układu, PDF.
4. [ ] Teksty w `submission/` i wiersz w `README.md`.
5. [ ] Bramka, PR, niezależny przegląd, merge.
