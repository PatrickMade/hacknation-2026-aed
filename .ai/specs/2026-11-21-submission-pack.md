# Pakiet zgłoszenia HackNation - teksty (wersja 1)

Issue: APP-47
Source doc: .ai/specs/2026-11-21-submission-pack.md
Route: agreed delivery (small change)

## Problem

Zgłoszenie do zadania "Misja AED - Dane na ratunek" wymaga tytułu i
szczegółowego opisu, prezentacji (co najmniej 5 slajdów z dowodami wymagań
technicznych, krokami użytkownika i ograniczeniami) oraz oświadczenia o
zakresie użycia AI (regulamin zadania, par. 2 ust. 8). W repozytorium nie ma
jeszcze żadnego z tych tekstów ani listy kontrolnej siedmiu rezultatów.

## Outcome

Nowy katalog `submission/` z tekstami, które nie wymagają zrzutów ekranu.
Język polski, pierwsza osoba liczby pojedynczej albo forma bezosobowa
(zespół jednoosobowy). Teksty opisują stan faktyczny: to, co jest gotowe,
i to, co jest w realizacji, oznaczają osobno.

## Scope

- `submission/README.md` - spis pakietu i lista elementów do uzupełnienia
  w wersji 2.
- `submission/opis-projektu.md` - tytuł, krótki opis, szczegółowy opis,
  teksty do pól formularza HackTribe.
- `submission/oswiadczenie-ai.md` - zakres użycia AI w podziale na obszary.
- `submission/ograniczenia.md` - lista ograniczeń prototypu.
- `submission/prezentacja-konspekt.md` - konspekt co najmniej 5 slajdów.
- `submission/lista-kontrolna.md` - 7 rezultatów z właścicielem i statusem
  oraz kontrola przed wysłaniem.

Non-goals: zrzuty ekranu, PDF prezentacji (do 10 MB), nagranie demo,
pliki marki, zmiany kodu portalu, upublicznienie repozytorium. Te elementy
trafią do drugiego PR po scaleniu modułów AED.

## Acceptance

1. Sześć plików z sekcji Scope istnieje (`ls submission/`).
2. Konspekt ma co najmniej 5 slajdów, w tym slajdy z dowodami wymagań
   technicznych, krokami użytkownika i ograniczeniami (`grep -c '^## Slajd'`).
3. Lista kontrolna wymienia 7 rezultatów z zadania, każdy z właścicielem
   i statusem.
4. Oświadczenie AI dzieli użycie na obszary i wskazuje rolę człowieka.
5. Brak form 1. osoby liczby mnogiej. Sprawdzenie: brak trafień
   `grep -n -i -w -E 'my|nas|nam|nasz[a-ząęóśłż]*|[a-ząćęłńóśźż]+śmy'`
   w `submission/` oraz ręczny odczyt wszystkich plików (formy na -my,
   np. "budujemy", grep nie odróżnia od słów typu "problemy").
6. Liczby i fakty zgadzają się z `aed-standard/` (43 pola, 15 wymaganych,
   3 warunkowe) i z materiałami badawczymi projektu.
7. Bramka `validation.commands` przechodzi; diff dotyka tylko `submission/`
   i tej specyfikacji.

## Verification

- `python3 -c` odczyt `aed-standard/schema.json`: liczba pól i wymagalność.
- grep z punktu 5 oraz ręczny odczyt.
- Pełna bramka z `.ai/agentic.config.json` raz na stabilnym kandydacie.
- QA: zmiana tylko dokumentacji, więc `skip-qa`.

## Progress

1. [x] Issue APP-47 i claim.
2. [x] Specyfikacja (ten plik).
3. [x] Teksty w `submission/`.
4. [x] Kontrole akceptacji i bramka walidacji.
5. [ ] PR, niezależny przegląd, merge gate.
