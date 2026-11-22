# Pakiet zgłoszenia HackNation 2026

Materiały zgłoszenia "Mapa Serc" do zadania "Misja AED - Dane na ratunek"
(Ministerstwo Cyfryzacji, Departament Zarządzania Danymi). Projekt
w HackTribe: https://hacknation2026.hacktribe.co/mapa-serc/

| Plik | Zawartość |
|---|---|
| [mapa-serc-prezentacja.pdf](mapa-serc-prezentacja.pdf) | Prezentacja zgłoszenia (PDF, 13 slajdów i 2 załączniki) |
| [mapa-serc-demo.mp4](mapa-serc-demo.mp4) | Nagranie demo: 1 min 57 s, muzyka bez lektora, napisy w obrazie i w pliku [mapa-serc-demo.srt](mapa-serc-demo.srt); opis montażu w [nagranie-demo.md](nagranie-demo.md) |
| [mapa-serc-okladka-hacktribe.png](mapa-serc-okladka-hacktribe.png) | Okładka projektu w HackTribe (800 x 600 px) |
| [prezentacja/](prezentacja/) | Źródła slajdów: HTML, CSS, zrzuty ekranu, krój pisma i skrypt budujący PDF; znak i plakat są czytane z `brand/` |
| [opis-projektu.md](opis-projektu.md) | Tytuł, krótki i szczegółowy opis, kroki użytkownika, teksty do formularza HackTribe |
| [oswiadczenie-ai.md](oswiadczenie-ai.md) | Zakres wykorzystania AI według obszarów (regulamin zadania, par. 2 ust. 8) |
| [ograniczenia.md](ograniczenia.md) | Ograniczenia prototypu |
| [akceptacja.md](akceptacja.md) | Lista akceptacji autora: demo, PDF, księga znaku, XLSX, oświadczenie AI, nagranie, decyzje o danych zgłaszających |
| [lista-kontrolna.md](lista-kontrolna.md) | Lista robocza: siedem wymaganych rezultatów ze statusem i kontrola przed wysłaniem; nie wchodzi do treści zgłoszenia |

Wzorcowy zakres danych AED (słownik XLSX, szablon, schemat, walidator)
znajduje się w [`aed-standard/`](../aed-standard/).

## Budowa PDF

```sh
python3 -B submission/prezentacja/build-pdf.py
```

Skrypt drukuje `prezentacja/slajdy.html` przez Chrome lub Chromium bez
interfejsu, sprawdza limit 10 MB oraz liczbę slajdów i zapisuje okładkę
HackTribe z `prezentacja/okladka.html`. Szczegóły:
[prezentacja/README.md](prezentacja/README.md).
