# Pakiet zgłoszenia HackNation - prezentacja PDF, zrzuty, nagranie (wersja 2)

Issue: APP-50
Source doc: .ai/specs/2026-11-21-submission-pack-2.md
Route: agreed delivery (small change, docs only)

## Problem

Zgłoszenie wymaga prezentacji PDF (najwyżej 10 MB, co najmniej 5 slajdów ze
zrzutami ekranu, krokami użytkownika i ograniczeniami) oraz zalecanego
nagrania demo do 2 minut. Wersja 1 tekstów (`.ai/specs/2026-11-21-submission-pack.md`)
zawiera znaczniki dla marki, stanu prototypu i dostępu do repozytorium.

## Outcome

- `submission/mapa-serc-prezentacja.pdf` w identyfikacji Mapa Serc, ze
  źródłami w `submission/prezentacja/` i skryptem `build-pdf.py`, który
  odtwarza PDF i sprawdza limit 10 MB oraz liczbę stron. Slajdy: problem,
  rozwiązanie, dowody wymagań technicznych ze zrzutami, kroki użytkownika,
  ograniczenia, użycie AI.
- Zrzuty ekranu i nagranie z lokalnej instancji portalu uruchomionej
  z `main`.
- `submission/akceptacja.md`: lista do akceptacji przez autora (demo lokalne,
  PDF, księga znaku, XLSX, oświadczenie AI, nagranie).
- Teksty wersji 1: nazwa i hasło "Mapa Serc", repozytorium publiczne, link
  HackTribe, aktualny stan modułów, wiersze oświadczenia AI dla modułów.
  Konspekt prezentacji zastępują źródła slajdów (plik usunięty).
- Nagranie demo MP4 do 2 minut w `submission/` oraz okładka projektu
  HackTribe 800 x 600 px.

Non-goals: scenariusz wystąpienia i pytania jury (dopiero po awansie do
pierwszej piątki), edycja formularza HackTribe, pliki marki, kod modułów.
Poprawka poza `submission/`: w `README.md` "nasze modyfikacje" zmienia się
na formę bezosobową (zasada zespołu jednoosobowego).

## Acceptance

1. `python3 -B submission/prezentacja/build-pdf.py` kończy się kodem 0;
   PDF ma co najmniej 5 stron i najwyżej 10 MB.
2. PDF zawiera slajdy: problem, rozwiązanie, dowody wymagań technicznych ze
   zrzutami, kroki dysponenta i odbiorcy, ograniczenia, użycie AI.
3. Liczby na slajdach zgadzają się ze źródłami: 43/15/3 pola
   (`aed-standard/schema.json`), 74 rekordy raportu i 18 298 punktów OSM
   (API lokalnej instancji), 21 rekordów Krosna (raport kreatora).
4. `submission/akceptacja.md` ma punkty dla demo lokalnego, PDF, księgi
   znaku, XLSX, oświadczenia AI i nagrania.
5. Brak form 1. osoby liczby mnogiej w `submission/` i w zmienionych
   liniach `README.md`; brak prywatnych ścieżek, identyfikatorów sesji,
   haseł.
6. Bramka `validation.commands` przechodzi.
7. Nagranie (gdy dodane): MP4, najwyżej 120 s.

## Verification

- `build-pdf.py`, `pdfinfo`, podgląd stron w niskiej rozdzielczości.
- grep form "my" i wzorców prywatnych danych.
- `ffprobe` długości nagrania.
- Pełna bramka raz na stabilnym kandydacie; QA: docs only, `skip-qa`.

## Progress

1. [x] Issue APP-50 i claim.
2. [x] Zrzuty ekranu z lokalnej instancji integracyjnej.
3. [x] Slajdy HTML, skrypt PDF, PDF.
4. [x] Aktualizacja tekstów wersji 1, `akceptacja.md`.
5. [ ] Bramka, PR, niezależny przegląd, merge.
6. [x] Zrzut strony akcji z licznikami i mapą (PR #6, head 01804b1).
7. [x] Nagranie demo MP4 (102,1 s) i zrzuty z instancji uruchomionej z `main`.
8. [x] Okładka HackTribe 800 x 600; kontrola axe-core nowych stron AED.
