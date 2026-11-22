# Końcowa poprawka prezentacji Mapa Serc

Issue: APP-68
Source doc: .ai/specs/2026-11-22-deck-final-touch.md
Route: agreed delivery (small change, docs only)
Extends: .ai/specs/2026-11-22-deck-refresh.md

## Problem

Niezależny przegląd PR #28 wskazał dwie drobne usterki i jedną lukę poza
jego zakresem; czas nagrania demo zmienia PR #23.

## Outcome

- `submission/prezentacja/img/zrzuty/kreator-kolumny.jpg` kończy się pod
  pełnym wierszem pól wyboru (bez uciętej dolnej krawędzi).
- `submission/lista-kontrolna.md`: skrót ograniczeń jest na slajdzie 13.
- `README.md`, krok demo "Kreator dysponenta": dla pliku Krosna dysponenta
  i datę danych wpisuje się ręcznie.
- Czas nagrania demo na slajdzie 14 zgadza się z plikiem
  `submission/mapa-serc-demo.mp4` w `main`: 1 min 57 s po scaleniu PR #23.
  Teksty w `submission/*.md` zmienił już PR #23.
- Podpis naklejki na slajdzie 12 i `submission/ograniczenia.md` mówią, że
  wiersz o numerze 112 ma wzór do druku z księgi znaku, a naklejka
  drukowana ze strony urządzenia w portalu jeszcze go nie ma.

Non-goals: kolejna runda jurorów, inne zmiany slajdów, kod portalu, pliki
marki, samo nagranie.

## Acceptance

1. `python3 -B submission/prezentacja/build-pdf.py` kończy się kodem 0.
2. Kontrola układu slajdów przechodzi; zrzut na slajdzie 4 nie ucina
   żadnego elementu.
3. Czas nagrania w tekstach równa się długości pliku MP4 w gałęzi
   (`ffprobe`), zaokrąglonej do sekundy.
4. Bramka `validation.commands` przechodzi.

## Progress

1. [x] Issue APP-68 i claim.
2. [x] Kadr, lista kontrolna, README.
3. [x] Czas nagrania 1 min 57 s po scaleniu PR #23 (plik w `main`: 116,8 s).
4. [ ] Bramka, PR, niezależny przegląd, merge.
