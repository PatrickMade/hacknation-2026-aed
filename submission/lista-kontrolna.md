# Lista kontrolna zgłoszenia

Lista robocza. Stan na 2026-11-21, 20:20 UTC. Termin finalnego zgłoszenia
w HackTribe: **2026-11-22, 10:00 UTC (11:00 czasu polskiego, CET)**. Po
terminie nie można zmieniać rozwiązania.

Statusy: **gotowe**, **w przeglądzie** (pull request czeka na przegląd
i scalenie), **w realizacji**, **do zrobienia**.

## Siedem wymaganych rezultatów

Wymagania z pełnej treści zadania, pkt 2-5.

| # | Rezultat | Wymaganie | Właściciel (obszar prac) | Status | Gdzie |
|---|---|---|---|---|---|
| 1 | Tytuł i szczegółowy opis | Tytuł i szczegółowy opis projektu | Pakiet zgłoszenia | gotowe; aktualizacja stanu po scaleniu modułów | `submission/opis-projektu.md` |
| 2 | Prezentacja | PDF do 10 MB, co najmniej 5 slajdów z dowodami wymagań technicznych (zrzuty ekranu), funkcjonalności, kroki użytkownika, ograniczenia | Pakiet zgłoszenia | gotowe: 14 slajdów; aktualizacja statusów po scaleniu PR #6 i PR #10 | `submission/mapa-serc-prezentacja.pdf`, źródła w `submission/prezentacja/` |
| 3 | Działający prototyp | Zbieranie danych AED z wielu źródeł do jednego maszynowo czytelnego zbioru w dane.gov.pl | Portal, raport zbiorczy, kreator, walidator, zgłoszenia i "Najbliższy AED" (w `main`); strona akcji (PR #6) | wszystko poza stroną akcji gotowe; strona akcji w przeglądzie | repozytorium, `README.md` |
| 4 | Wzorcowy zakres danych | Tabela w formacie XLSX | Wzorcowy zakres danych | gotowe | `aed-standard/field-dictionary.xlsx` |
| 5 | Kod źródłowy | Kod źródłowy rozwiązania | Wszystkie obszary | gotowe: repozytorium publiczne; moduły w przeglądzie | https://github.com/PatrickMade/hacknation-2026-aed |
| 6 | Nazwa akcji, hasło, logo, księga znaku | Logo w .jpg, .png, .pdf i formacie otwartym (np. .svg); księga znaku PDF: kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia, opis koncepcji w 3-5 zdaniach | Marka akcji "Mapa Serc" (PR #10) | w przeglądzie | `brand/` po scaleniu |
| 7 | Oświadczenie o użyciu AI | Zakres wykorzystania AI (regulamin zadania, par. 2 ust. 8) | Pakiet zgłoszenia | gotowe; aktualizacja po scaleniu modułów | `submission/oswiadczenie-ai.md` |

## Elementy uzupełniające

| Element | Status | Uwagi |
|---|---|---|
| Lista ograniczeń | gotowe | `submission/ograniczenia.md`; skrót na slajdzie 12 |
| Nagranie demo | do zrobienia | Plik MP4 do 2 minut w `submission/`, materiał dodatkowy w HackTribe; bez serwisów wideo |
| Lista akceptacji autora | gotowe do akceptacji | `submission/akceptacja.md` |

## Pola formularza HackTribe

Projekt: https://hacknation2026.hacktribe.co/mapa-serc/

| Pole | Status | Źródło treści |
|---|---|---|
| Nazwa projektu, zadanie, zespół, stolik | gotowe | "Mapa Serc", zadanie "Misja AED - Dane na ratunek" |
| Problem, rozwiązanie, krótki opis | gotowe do wklejenia | `opis-projektu.md`, sekcje Krótki opis i Teksty do formularza HackTribe |
| Link do repozytorium | gotowe | Repozytorium publiczne |
| Prezentacja PDF | do wgrania | `submission/mapa-serc-prezentacja.pdf` (do 10 MB) |
| Materiały dodatkowe | do wgrania | XLSX, pliki logo, księga znaku, nagranie MP4 |

## Kontrola przed wysłaniem

- [ ] Pull requesty modułów AED i marki scalone; `main` przechodzi bramkę
      walidacji.
- [ ] Prototyp uruchomiony od zera według `README.md`; demo przechodzi
      kroki z `akceptacja.md`.
- [ ] PDF prezentacji ma co najmniej 5 slajdów i najwyżej 10 MB
      (`python3 -B submission/prezentacja/build-pdf.py`).
- [x] Logo w .jpg, .png, .pdf i .svg; księga znaku w PDF z wymaganymi
      sekcjami (`brand/`).
- [ ] Opis, ograniczenia, oświadczenie AI i slajdy odpowiadają scalonemu
      stanowi: `grep -rin -E "do uzupełnienia|do wykonania|w realizacji|w przeglądzie" submission/*.md submission/prezentacja/slajdy.html`
      nie zwraca wyników poza tą listą.
- [ ] Teksty w pierwszej osobie liczby pojedynczej lub bezosobowo.
- [ ] Wszystkie linki w zgłoszeniu działają.
- [ ] Repozytorium nie zawiera haseł ani prywatnych danych; informacje
      o licencji GPLv3 portalu i ODbL dla OSM są na miejscu.
- [ ] Autor zaakceptował wszystkie punkty `akceptacja.md`.
- [ ] Zgłoszenie zapisane w HackTribe przed 10:00 UTC.
