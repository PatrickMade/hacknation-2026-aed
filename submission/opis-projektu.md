# Opis projektu

## Tytuł

**Mapa Serc - jeden standard danych o defibrylatorach AED w dane.gov.pl**

Zadanie: "Misja AED - Dane na ratunek" (Ministerstwo Cyfryzacji, Departament
Zarządzania Danymi). Zespół jednoosobowy.

Nazwa i hasło akcji: **Mapa Serc - „Wszystkie AED pod ręką.”** Zdanie dla
dysponentów: „Lista AED w szufladzie nikogo nie uratuje.”

Kod: https://github.com/PatrickMade/hacknation-2026-aed (repozytorium
publiczne). Projekt w HackTribe: https://hacknation2026.hacktribe.co/mapa-serc/

## Krótki opis

Każdy dysponent defibrylatora (gmina, szpital, szkoła, uczelnia, firma,
straż, policja, przewoźnik) może w kilka minut opublikować dane o swoich AED
w portalu dane.gov.pl, w jednym wspólnym standardzie. Portal sam łączy te
dane w ogólnopolski raport zbiorczy AED, dostępny w API, na mapie i do
pobrania dla służb ratunkowych, twórców aplikacji i obywateli. Akcja z własną
nazwą, hasłem i znakiem zachęca dysponentów do udostępniania danych, a ten
sam znak z kodem QR przy urządzeniu prowadzi do jego wpisu i do zgłoszenia
problemu.

## Problem

Dane o AED w Polsce są rozproszone i niespójne:

- w dane.gov.pl jest tylko kilka zbiorów AED (Krosno, Marki, Przemyśl,
  Warszawa, Legionowo) i każdy ma inny układ kolumn. W zbiorze z Marek cały
  rekord jest zakodowany w jednej kolumnie CSV, a współrzędne są w większości
  zamienione miejscami;
- na stronach urzędów zebrałem 739 wpisów o AED z 20 źródeł (HTML, PDF,
  mapy). Tylko 137 z nich ma współrzędne geograficzne;
- OpenStreetMap zna ponad 18 tysięcy punktów AED w Polsce, ale to dane
  społecznościowe na licencji ODbL, bez wskazania odpowiedzialnego dysponenta.

Dyspozytor 112, ratownik albo autor aplikacji nie ma jednego, aktualnego
i maszynowo czytelnego źródła, które mówi, gdzie jest AED, kiedy jest
dostępny i kto za niego odpowiada.

## Rozwiązanie

Rozwiązaniem jest **mechanizm zbierania danych AED wewnątrz portalu
dane.gov.pl**, a nie osobna aplikacja z mapą. Pracuję na oficjalnym, otwartym
kodzie portalu (backend 2.62.3, frontend 3.5.2, licencja GPLv3), uruchomionym
lokalnie. Wygląd, treści i układ portalu poza obszarami AED pozostają bez
zmian; nowe ekrany używają istniejących komponentów portalu.

Za dane o urządzeniu odpowiada jego dysponent. Dlatego każdy dysponent
publikuje własny zbiór AED w swojej instytucji w portalu, a zbiór
ogólnopolski powstaje automatycznie jako **raport zbiorczy**, na wzór
istniejącego w portalu zbioru "Wykaz zasobów chronionych danych DGA - raport
zbiorczy" (zbiór 4354). Wydawcą raportu jest Ministerstwo Cyfryzacji jako
operator portalu. Każdy rekord wskazuje dysponenta jako odpowiedzialnego
i prowadzi do jego zbioru źródłowego.

### Elementy rozwiązania

1. **Wzorcowy zakres danych AED** (`aed-standard/`): słownik 43 pól w XLSX
   (15 wymaganych, 3 warunkowe, 25 opcjonalnych), szablon CSV, schemat
   maszynowy Table Schema, przykładowy rekord, mapowania pięciu istniejących
   zbiorów i OSM oraz walidator z testami. Lokalizacja w WGS84, adres z kodami
   TERYT, opis miejsca, dostępność i godziny w notacji `opening_hours`,
   dysponent, przegląd, stan urządzenia, pochodzenie i licencja każdego
   rekordu. Bez danych osobowych: tylko kontakt instytucjonalny.
2. **Kreator dysponenta** w panelu dostawcy portalu: pobranie szablonu,
   wgranie pliku CSV, XLSX lub GeoJSON albo podanie adresu URL, dopasowanie
   kolumn do standardu, raport walidacji z błędami wskazanymi do wiersza
   i pola, publikacja zasobu z gotowymi metadanymi (kategoria Zdrowie, słowo
   kluczowe AED, częstotliwość aktualizacji, licencja, data danych) i znakiem
   zgodności ze standardem.
3. **Publiczny walidator "sprawdź swój plik"**: bez logowania i bez
   zapisywania pliku.
4. **Agregator i raport zbiorczy AED**: mapowanie istniejących układów do
   standardu, walidacja, deduplikacja z zachowaniem pochodzenia rekordu,
   flagi jakości (np. zamienione współrzędne). Zasoby raportu: CSV
   ze współrzędnymi, z którego korzysta wbudowana mapa portalu, GeoJSON do
   pobrania oraz punkty AED z OSM jako osobny zasób na licencji ODbL.
   Odświeżanie: zadanie okresowe w tle, w demo uruchamiane ręcznie.
5. **Strona akcji w portalu**: kampania, liczniki (dysponenci, rekordy AED,
   gminy z danymi na tle 2479 gmin), mapa pokrycia gmin z lukami ("OSM zna
   AED, wpisu urzędowego brak") i przycisk prowadzący do kreatora.
6. **Zgłoszenie problemu do konkretnego dysponenta**: kod QR na naklejce przy
   AED prowadzi do wpisu urządzenia i formularza "Zgłoś problem" (zamknięty,
   brak urządzenia, uszkodzony, złe dane lub lokalizacja). Kontakt do
   zgłaszającego jest opcjonalny i wymaga wyraźnej zgody (RODO). Zgłoszenie
   trafia do panelu właściwego dysponenta ze statusem nowe, w trakcie,
   rozwiązane.
7. **"Najbliższy AED"**: wpis w zakładce PoCoTo portalu, oparty na
   istniejącym filtrze odległości mapy portalu i raporcie zbiorczym.

### Kroki użytkownika

**Dysponent AED** (np. urzędnik gminy):

1. Loguje się do panelu dostawcy portalu i wybiera "Dodaj dane AED".
2. Pobiera szablon albo wgrywa własny plik lub podaje URL.
3. Dopasowuje kolumny pliku do pól standardu.
4. Czyta raport walidacji i poprawia wskazane błędy.
5. Publikuje zasób z uzupełnionymi metadanymi. Rekordy trafiają do raportu
   zbiorczego przy najbliższym odświeżeniu.
6. Odbiera zgłoszenia problemów ze swoimi urządzeniami w panelu i zmienia ich
   status.

**Odbiorca danych** (dyspozytor, twórca aplikacji, obywatel):

1. Otwiera zbiór "Raport zbiorczy AED" w portalu.
2. Przegląda punkty na mapie albo pobiera CSV lub GeoJSON.
3. Pobiera rekordy przez API portalu (`/1.4/resources/{id}/data`).
4. Przy urządzeniu skanuje kod QR i zgłasza problem jego dysponentowi.

## Zgodność z zasadami dane.gov.pl

- Publikacja przez standardowe mechanizmy portalu: instytucja, zbiór, zasób,
  panel dostawcy, API. Ta sama ścieżka działa w produkcyjnym dane.gov.pl;
  w prototypie niczego nie publikuję na produkcji.
- Formaty maszynowo czytelne: CSV (UTF-8, RFC 4180), GeoJSON, JSON z API,
  słownik XLSX. Bez PDF i DOC jako formatu danych.
- Wymagane metadane zbioru i zasobu: opis, instytucja, kategoria, słowa
  kluczowe, częstotliwość aktualizacji, warunki ponownego wykorzystania,
  data danych.
- Licencje: dane dysponentów na licencjach otwartych wybranych przy
  publikacji (np. CC0 1.0, CC BY 4.0), OSM osobno na ODbL 1.0 z atrybucją
  "© OpenStreetMap contributors".
- Mapa portalu: kolumny `longitude`, `latitude`, `name` przypisane do ról
  `l`, `b`, `label`.
- Nowe strony AED: projektowane pod WCAG 2.2 na poziomie AA, układ
  responsywny od 360 px. Wynik automatycznej kontroli dostępności opisuje
  `ograniczenia.md`.

## Architektura i technologie

Oficjalny kod portalu dane.gov.pl: Django, Falcon API 1.4, Wagtail CMS,
Celery, PostgreSQL, Elasticsearch, Redis, RabbitMQ, Apache Jena Fuseki,
nginx oraz frontend Angular z mapą Leaflet. Całość uruchamia jedna
konfiguracja Docker Compose z danymi startowymi: instytucje dysponentów
i konta o różnych rolach (administrator, edytorzy instytucji, zwykły
użytkownik). Moduły AED to nowe aplikacje Django w backendzie i nowe trasy
we frontendzie portalu. Walidacja w portalu korzysta z tego samego schematu
i walidatora co pakiet `aed-standard/`.

Jury uruchamia prototyp lokalnie z kodu. Instrukcja: `README.md`
w repozytorium.

## Stan prototypu

Stan na 2026-11-21, 22:27 UTC: wszystkie elementy są w gałęzi `main`.

| Element | Stan |
|---|---|
| Wzorcowy zakres danych `aed-standard/` | gotowy, w `main` |
| Lokalny portal dane.gov.pl z kontami | gotowy, w `main` |
| Agregator i raport zbiorczy AED | gotowy, w `main` |
| Kreator dysponenta i walidator | gotowy, w `main` |
| Strona akcji i mapa pokrycia | gotowe, w `main` |
| Zgłoszenia problemów, QR, "Najbliższy AED" | gotowe, w `main` |
| Nazwa, hasło, logo, księga znaku (`brand/`) | gotowe, w `main` |
| Prezentacja PDF i nagranie demo (`submission/`) | gotowe |

Ograniczenia: `ograniczenia.md`. Użycie AI: `oswiadczenie-ai.md`.

## Teksty do formularza HackTribe

**Problem:** Dane o defibrylatorach AED w Polsce są rozproszone: kilka
niespójnych zbiorów w dane.gov.pl, setki wpisów na stronach urzędów
w HTML i PDF, w większości bez współrzędnych. Służby, twórcy aplikacji
i obywatele nie mają jednego aktualnego, maszynowo czytelnego źródła, które
mówi, gdzie jest AED, kiedy jest dostępny i kto za niego odpowiada.

**Rozwiązanie:** Mechanizm w portalu dane.gov.pl, na jego oficjalnym kodzie:
wzorcowy zakres danych AED (43 pola, XLSX, CSV, schemat), kreator, w którym
dysponent wgrywa plik, dopasowuje kolumny, poprawia błędy i publikuje dane
we własnym zbiorze, oraz automatyczny raport zbiorczy AED z mapą, API
i pochodzeniem każdego rekordu. Zgłoszenia problemów z urządzeniem trafiają
wprost do jego dysponenta, a akcja z własnym znakiem i kodem QR zachęca
dysponentów do publikacji.
