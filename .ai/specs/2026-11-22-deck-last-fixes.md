# Ostatnie poprawki prezentacji Mapa Serc przed wysłaniem

Issue: APP-74
Source doc: .ai/specs/2026-11-22-deck-last-fixes.md
Route: agreed delivery (small change, docs only)
Extends: .ai/specs/2026-11-22-deck-final-touch.md

## Problem

Autor zaakceptował ostatnie poprawki prezentacji przed terminem
zgłoszenia (2026-11-22 10:00 UTC).

## Outcome

- Slajd 2: tytuł mówi, że w otwartych danych nie ma jednego rejestru AED
  (zamiast "nikt nie wie, gdzie są wszystkie AED").
- Załącznik A (slajd 15) i `submission/ograniczenia.md`: trzy uwagi
  dostępności w niezmienionej powłoce portalu (odnośnik menu, pasek
  postępu, fokus w oknie RODO i plików cookie).
- Slajd 7: pod tabelą zdanie, że Kraków, Poznań i Gdańsk mają w prototypie
  tylko fikcyjne rekordy demonstracyjne i nadal są lukami.
- Slajd 14: kody QR odczytane z renderu PDF prowadzą do publicznego
  repozytorium i do pliku MP4 w tym repozytorium.

- Czas nagrania demo: 1 min 59 s na slajdzie 14 i w tekstach
  `submission/`, zgodnie z plikiem po ponownym renderze nagrania (118,8 s).

Non-goals: runda jurorów, inne slajdy, kod portalu, nagranie.

## Acceptance

1. `python3 -B submission/prezentacja/build-pdf.py` kończy się kodem 0;
   PDF ma najwyżej 10 MB.
2. Kontrola układu slajdów przechodzi.
3. Oba kody QR ze slajdu 14 odczytane z renderu PDF dają oczekiwane adresy.
4. Czas nagrania w tekstach równa się długości pliku MP4 w `main` po
   scaleniu zmiany nagrania (`ffprobe`), zaokrąglonej do sekundy.
5. Bramka `validation.commands` przechodzi.

## Progress

1. [x] Issue APP-74 i claim.
2. [x] Slajdy 2, 7, 15 i `ograniczenia.md`.
3. [x] Kody QR odczytane z renderu PDF.
4. [ ] Bramka, PR, niezależny przegląd, merge.
