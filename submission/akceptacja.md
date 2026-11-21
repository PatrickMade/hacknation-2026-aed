# Lista akceptacji autora

Każdy punkt akceptuje autor po własnym sprawdzeniu. Zaznacz `[x]` i wpisz
uwagi albo "OK". Punkt z uwagami wraca do poprawy przed wysłaniem
zgłoszenia.

Stan na 2026-11-21, 19:50 UTC. Punkty zależne od niescalonych jeszcze
pull requestów są oznaczone numerem PR.

## 1. Demo lokalne

Uruchomienie według `README.md` (sekcja "Uruchomienie od zera"), potem:

- [ ] 1.1 Portal działa pod https://mcod.local/ bez zmian wyglądu poza
      obszarami AED.
- [ ] 1.2 Zbiór "Raport zbiorczy AED" ma zasoby CSV, GeoJSON i OSM (ODbL);
      zakładka Mapa pokazuje punkty.
- [ ] 1.3 API zwraca rekordy raportu: `https://api.mcod.local/1.4/resources/<id CSV>/data`.
- [ ] 1.4 Kreator: konto pełnomocnika Krosna, "Dodaj dane AED",
      plik Krosna, przypisanie kolumn, raport walidacji, publikacja.
- [ ] 1.5 Walidator "Sprawdź swój plik" pokazuje błędy pliku
      z błędami bez logowania.
- [ ] 1.6 Karta urządzenia i "Zgłoś problem" (PR #7): zgłoszenie widzi tylko
      dysponent urządzenia, e-mail w MailHog.
- [ ] 1.7 Strona akcji `/pl/aed` (PR #6): liczniki i mapa pokrycia gmin,
      także na telefonie.
- [ ] 1.8 "Najbliższy AED" w zakładce PoCoTo (PR #7).

Uwagi:

## 2. Prezentacja PDF

`submission/mapa-serc-prezentacja.pdf`

- [ ] 2.1 Treść slajdów zgodna z prototypem i opisem.
- [ ] 2.2 Zrzuty ekranu aktualne (strona akcji z licznikami po PR #6).
- [ ] 2.3 Slajd 10: wynik kontroli dostępności nowych stron AED zamiast
      znacznika "do uzupełnienia" (po przeglądzie integracyjnym).
- [ ] 2.4 Rozmiar do 10 MB, co najmniej 5 slajdów.

Uwagi:

## 3. Księga znaku

`brand/ksiega-znaku-mapa-serc.pdf` (PR #10)

- [ ] 3.1 Kolorystyka, pole ochronne, minimalna wielkość, niedozwolone
      użycia, opis koncepcji w 3-5 zdaniach.
- [ ] 3.2 Logo w .jpg, .png, .pdf i .svg; nazwa "Mapa Serc", hasło
      "Wszystkie AED pod ręką."

Uwagi:

## 4. Wzorcowy zakres danych (XLSX)

`aed-standard/field-dictionary.xlsx`

- [ ] 4.1 43 pola z polską etykietą, typem, wymagalnością, formatem,
      przykładem i opisem.
- [ ] 4.2 Brak danych osobowych w zakresie; kontakt tylko instytucjonalny.

Uwagi:

## 5. Oświadczenie o użyciu AI

`submission/oswiadczenie-ai.md`

- [ ] 5.1 Zakres użycia AI w każdym obszarze jest prawdziwy i kompletny.
- [ ] 5.2 Rola człowieka i odpowiedzialność autora opisane zgodnie ze stanem
      faktycznym.

Uwagi:

## 6. Nagranie demo

`submission/` (plik MP4, do 2 minut)

- [ ] 6.1 Nagranie pokazuje kroki dysponenta i odbiorcy danych.
- [ ] 6.2 Długość do 2 minut; brak haseł i prywatnych danych na ekranie.

Uwagi:
