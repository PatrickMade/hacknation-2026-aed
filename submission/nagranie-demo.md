# Nagranie demo - notatka montażowa

Plik: [mapa-serc-demo.mp4](mapa-serc-demo.mp4), napisy:
[mapa-serc-demo.srt](mapa-serc-demo.srt).

| Parametr | Wartość |
|---|---|
| Czas trwania | 1 min 57 s |
| Obraz | 1920x1080, 30 kl./s, H.264 (High), yuv420p |
| Dźwięk | AAC 48 kHz stereo, sama muzyka, bez lektora; -16,0 LUFS, szczyt -3,4 dBFS |
| Napisy | polskie, wypalone w obrazie; ten sam tekst w pliku `.srt` |
| Rozmiar pliku | 14,6 MB |

## Układ nagrania

| Czas | Część | Co widać |
|---|---|---|
| 0:00-0:18 | Problem | Plansze: ile gmin ma oficjalne dane o AED, pięć zbiorów AED w dane.gov.pl i ich układy, jeden zbiór w 43 polach wzorcowego zakresu danych, znak akcji |
| 0:18-0:38 | 1. Dysponent publikuje dane | Kreator "Dodaj dane AED": plik Krosna, przypisanie kolumn, wynik walidacji, publikacja |
| 0:38-1:05 | 2. Raport zbiorczy: mapa i API | Zbiór "Raport zbiorczy AED", zasoby, licencja, mapa portalu, tabela, odpowiedź API |
| 1:05-1:35 | 3. Zgłoszenie z kodu QR | Naklejka i karta urządzenia na telefonie, formularz zgłoszenia, panel dysponenta, e-mail |
| 1:35-1:47 | 4. Strona akcji | Strona Mapa Serc: liczniki, mapa luk, przykład Warszawy |
| 1:47-1:57 | Wezwanie do działania | Plansza końcowa z adresem repozytorium i kodem QR |

## Jak powstało

1. **Nagrania ekranu.** Wszystkie ujęcia portalu pochodzą z lokalnej
   instancji uruchomionej według `README.md` (Docker Compose, konta i dane
   demonstracyjne z poleceń opisanych w README). Przeglądarkę prowadzi skrypt
   Playwright: klika, przewija i wpisuje tekst w prawdziwym interfejsie.
   Obraz jest zapisywany w rozdzielczości 2560x1440 (telefon: 1125x2001),
   a ruch kursora i przewijanie klatka po klatce w 30 kl./s. Kursor i kółko
   dotyku dorysowuje skrypt, bo przeglądarka bez okna ich nie pokazuje.
   Treści stron nie zmieniano. Odpowiedź API pokazuje wbudowany podgląd JSON
   przeglądarki z włączonym formatowaniem.
2. **Kolejność zdarzeń.** Najpierw publikacja pliku w kreatorze, potem
   `aed_refresh`, a dopiero po nim nagrania raportu zbiorczego, mapy, tabeli
   i API. Raport w nagraniu obejmuje więc także plik opublikowany w kreatorze.
3. **Grafiki.** Plansza otwierająca, plansza końcowa, ramka z numerem kroku,
   obwódki i napisy są renderowane z HTML i CSS w kolorach z
   `brand/tokens.css`, krojem Figtree i gotowymi plikami znaku z
   `brand/logo/`. Liczby na planszy otwierającej są odczytane ze strony akcji
   w chwili nagrania. Nagłówki plików na planszy "pięć zbiorów" są przepisane
   z `backend/data/aed/sources/`. Naklejka obok telefonu to zrzut naklejki,
   którą strona urządzenia pokazuje dysponentowi: jej kod QR prowadzi do tej
   samej karty urządzenia. Kod QR na planszy końcowej wygenerował koder z
   `backend/mcod/aed_reports/qr.py`.
4. **Montaż.** DaVinci Resolve Studio 21.1, sterowany przez serwer MCP
   `davinci-resolve` i skrypt korzystający z tego samego API skryptowego:
   projekt 1080p 30 kl./s, pięć ścieżek wideo (nagrania, ramka, obwódki,
   napisy, plansze) i ścieżka muzyki. Zbliżenia to przycięcia nagrań
   2560x1440, bez powiększania ponad rozdzielczość źródła. Lista cięć,
   teksty napisów i plik `.srt` pochodzą z jednej listy montażowej, więc
   napisy w obrazie i w pliku są tym samym tekstem.
5. **Eksport.** Resolve renderuje plik H.264; końcowe kodowanie do
   publikacji (x264, CRF 20, `+faststart`) wykonuje ffmpeg.

Pliki robocze (nagrania źródłowe, projekt Resolve, skrypty) nie są częścią
repozytorium.

## Dane w nagraniu

- Zbiory źródłowe: datowane kopie pięciu zbiorów AED z dane.gov.pl
  (`backend/data/aed/sources/`, licencje w `LICENSES.md`) oraz punkty AED
  z OpenStreetMap (ODbL 1.0).
- Plik wgrywany w kreatorze to kopia zbioru Krosna
  (`backend/data/aed/sources/krosno/Defibrylator_jAmxQcp.csv`, CC0 1.0).
- Urządzenie na karcie z kodem QR i zgłoszenie są przykładowe. Konta,
  instytucje i adresy e-mail pochodzą z `seed_jury`.
- Liczby w napisach są odczytane z ekranu w chwili nagrania: 21
  rekordów w kreatorze, 74 rekordy w API, 5 z
  2479 gmin z oficjalnymi danymi, 2123 gmin, w których AED zna
  tylko OpenStreetMap (stan raportu na 21.11.2026).

## Muzyka

Utwór instrumentalny wygenerowany w Suno (model v6) na koncie autora
w planie Pro, który według warunków Suno obejmuje prawa do komercyjnego
wykorzystania utworów. W nagraniu użyto skróconej wersji: dwa naturalne
wyciszenia utworu połączono w jedno, głośność wyrównano do -16,0 LUFS.
Plik muzyki nie jest osobno częścią repozytorium.

## Zakres użycia AI

Scenariusz, teksty napisów, skrypty nagrywające, grafiki, muzykę i montaż
przygotowano z użyciem AI (Claude, Anthropic; muzyka: Suno). Autor zatwierdza
treść i odpowiada za zgodność z działaniem prototypu. Ujęcia portalu są
nagraniami działającego kodu, nie obrazami wygenerowanymi przez AI.
Całość zakresu opisuje [oświadczenie o wykorzystaniu AI](oswiadczenie-ai.md).

## Sprawdzenie

```sh
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height submission/mapa-serc-demo.mp4
ffmpeg -hide_banner -nostats -i submission/mapa-serc-demo.mp4 -af ebur128 -f null - 2>&1 | tail -12
```
