# Scenariusz wystąpienia i pytania jury dla Mapy Serc

Issue: APP-75
Source doc: .ai/specs/2026-11-22-pitch-materials.md
Route: agreed delivery (small change, docs only)

## Problem

Finaliści HackNation 2026 występują na żywo 2026-11-22 od 14:15 UTC.
Autor nie ma scenariusza 5-minutowego wystąpienia ani przygotowanych
odpowiedzi na pytania jury. W finale HackNation 2025 jury poprosiło o pokaz
wybranego przypadku użycia na żywo zamiast przygotowanej prezentacji.

## Outcome

Nowy katalog `submission/pitch/`:

- `scenariusz.md`: wystąpienie na 5 minut, zaczynające się od pokazu na
  żywo; trzy scenariusze na lokalnym portalu z czasem, adresami i kontami;
  co mówić; lista przygotowań; plan awaryjny (nagranie, PDF); tabela
  "jury wybiera przypadek użycia".
- `pytania-jury.md`: prawdopodobne pytania z krótkimi odpowiedziami,
  z liczbami i ograniczeniami zgodnymi z `main`.
- Wiersz o katalogu w `submission/README.md`.

Non-goals: zmiany prezentacji PDF, nagrania, kodu portalu, formularza
HackTribe; próba wystąpienia.

Założenie: format finału (czas, przebieg) nie jest potwierdzony; scenariusz
zakłada 5 minut i przewiduje pokaz przypadku wybranego przez jury.

## Poprawka po próbie na działającym portalu (APP-76, 2026-11-22)

Próba scenariusza na lokalnej instancji z `main` 9c5696b pokazała trzy luki
w `scenariusz.md`; poprawka dopisuje je do tekstu:

- suwak promienia filtra odległości zaczyna od 0,1 km i wtedy filtr nic nie
  znajduje; w scenariuszu 2 trzeba go przesunąć na 0,5 km albo 1 km;
- po starcie usług tabela punktów OpenStreetMap indeksuje się jeszcze około
  2 minut, choć kolejki są puste;
- dwa konta panelu wymagają dwóch profili przeglądarki albo okna prywatnego.

Sprawdzenie: zachowanie lokalnej instancji; kod suwaka
(`frontend/src/app/shared/slider/slider.component.ts`).

## Acceptance

1. Suma czasów w scenariuszu wynosi najwyżej 5 minut.
2. Adresy, konta, polecenia i liczby zgadzają się z `README.md`,
   `submission/` i kodem w `main` (d22bcd8).
3. Teksty w pierwszej osobie liczby pojedynczej lub bezosobowo; brak
   prywatnych ścieżek, haseł i identyfikatorów sesji.
4. Bramka `validation.commands` przechodzi.

## Progress

1. [x] Issue APP-75 i claim.
2. [x] `scenariusz.md`, `pytania-jury.md`, wiersz w `submission/README.md`.
3. [ ] Bramka, PR, niezależny przegląd, merge.
