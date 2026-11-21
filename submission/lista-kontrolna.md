# Lista kontrolna zgłoszenia

Stan na 2026-11-21. Termin finalnego zgłoszenia w HackTribe:
**2026-11-22, 10:00 UTC (11:00 czasu polskiego, CET)**. Po terminie nie
można zmieniać rozwiązania.

Statusy: **gotowe**, **w przeglądzie** (pull request czeka na przegląd
i scalenie), **w realizacji**, **do zrobienia**.

## Siedem wymaganych rezultatów

Wymagania z pełnej treści zadania, pkt 2-5.

| # | Rezultat | Wymaganie | Właściciel (obszar prac) | Status | Gdzie |
|---|---|---|---|---|---|
| 1 | Tytuł i szczegółowy opis | Tytuł i szczegółowy opis projektu | Pakiet zgłoszenia (APP-47) | w przeglądzie (wersja 1); aktualizacja po scaleniu modułów AED | `submission/opis-projektu.md` |
| 2 | Prezentacja | PDF do 10 MB, co najmniej 5 slajdów z dowodami wymagań technicznych (zrzuty ekranu), funkcjonalności, kroki użytkownika, ograniczenia | Pakiet zgłoszenia (APP-47) | w realizacji: konspekt gotowy, zrzuty i PDF do zrobienia | `submission/prezentacja-konspekt.md` |
| 3 | Działający prototyp | Zbieranie danych AED z wielu źródeł do jednego maszynowo czytelnego zbioru w dane.gov.pl | Lokalny portal (APP-42); agregator (`backend/mcod/aed_aggregate/`); kreator i walidator (APP-43); strona akcji (APP-44); zgłoszenia i "Najbliższy AED" (`backend/mcod/aed_reports/`) | portal w przeglądzie; moduły AED w realizacji | repozytorium, `README.md` |
| 4 | Wzorcowy zakres danych | Tabela w formacie XLSX | Wzorcowy zakres danych (APP-41) | gotowe | `aed-standard/field-dictionary.xlsx` |
| 5 | Kod źródłowy | Kod źródłowy rozwiązania | Wszystkie obszary | w realizacji; dostęp jury do repozytorium do zrobienia | repozytorium GitHub |
| 6 | Nazwa akcji, hasło, logo, księga znaku | Logo w .jpg, .png, .pdf i formacie otwartym (np. .svg); księga znaku PDF: kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia, opis koncepcji w 3-5 zdaniach | Marka akcji (APP-48) | w przeglądzie: nazwa "Mapa Serc", hasło "Wszystkie AED pod ręką." | `brand/` |
| 7 | Oświadczenie o użyciu AI | Zakres wykorzystania AI (regulamin zadania, par. 2 ust. 8) | Pakiet zgłoszenia (APP-47) | w przeglądzie (wersja 1); wiersz o znaku uzupełniony | `submission/oswiadczenie-ai.md` |

## Elementy uzupełniające

| Element | Status | Uwagi |
|---|---|---|
| Lista ograniczeń | w przeglądzie (wersja 1) | `submission/ograniczenia.md`; trafia też na slajd 9 |
| Nagranie demo | do zrobienia | Zalecane do 2 minut; nieobowiązkowe |
| Zrzuty ekranu | do zrobienia | Lista w konspekcie prezentacji, po scaleniu modułów AED |

## Pola formularza HackTribe

| Pole | Status | Źródło treści |
|---|---|---|
| Nazwa projektu | do zrobienia: aktualizacja po wyborze nazwy akcji | `opis-projektu.md`, sekcja Tytuł |
| Nazwa zespołu, numer stolika | do zrobienia: uzupełnia autor | - |
| Zadanie partnerskie | do sprawdzenia: przypisane w drafcie (termin draftu 2026-11-21, 19:00 UTC) | "Misja AED - Dane na ratunek" |
| Problem, rozwiązanie, krótki opis | gotowe do wklejenia (wersja 1) | `opis-projektu.md`, sekcje Krótki opis i Teksty do formularza HackTribe |
| Link do repozytorium | do zrobienia: dostęp dla jury | Repozytorium staje się publiczne wyłącznie za zgodą autora, przed terminem |
| Prezentacja PDF | do zrobienia | Maksymalnie 10 MB |
| Materiały dodatkowe | do zrobienia | XLSX, pliki logo, księga znaku, nagranie |

## Kontrola przed wysłaniem

- [ ] Wszystkie pull requesty modułów AED scalone; `main` przechodzi bramkę
      walidacji.
- [ ] Prototyp uruchomiony od zera według `README.md`; demo przechodzi
      wszystkie kroki z konspektu.
- [ ] PDF prezentacji ma co najmniej 5 slajdów i najwyżej 10 MB.
- [ ] Logo w .jpg, .png, .pdf i .svg; księga znaku w PDF z wymaganymi
      sekcjami.
- [ ] Opis, ograniczenia i oświadczenie AI odpowiadają scalonemu stanowi;
      brak znaczników "do uzupełnienia", "do wykonania" i "w realizacji"
      w `opis-projektu.md`, `ograniczenia.md` i `oswiadczenie-ai.md`.
- [ ] Teksty w pierwszej osobie liczby pojedynczej lub bezosobowo.
- [ ] Wszystkie linki w zgłoszeniu działają, w tym dostęp jury do
      repozytorium.
- [ ] Repozytorium nie zawiera haseł ani prywatnych danych; informacje
      o licencji GPLv3 portalu i ODbL dla OSM są na miejscu.
- [ ] Przegląd końcowy wszystkich materiałów przez autora.
- [ ] Zgłoszenie zapisane w HackTribe przed 10:00 UTC.
