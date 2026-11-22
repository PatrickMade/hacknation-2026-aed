# Lista akceptacji autora

Każdy punkt akceptuje autor po własnym sprawdzeniu. Zaznacz `[x]` i wpisz
uwagi albo "OK". Punkt z uwagami wraca do poprawy przed wysłaniem
zgłoszenia.

Stan na 2026-11-21, 22:27 UTC. Wszystkie sprawdzane elementy są w gałęzi `main`.

## 1. Demo lokalne

Uruchomienie według `README.md`: sekcja "Uruchomienie od zera", a dla
punktów 1.6 i 1.8 także "Zgłoszenia AED i kody QR"
(`load_aed_report_devices` po `aed_refresh`, `load_aed_devices`,
`seed_aed_showcase`). Potem:

- [ ] 1.1 Portal działa pod https://mcod.local/ bez zmian wyglądu poza
      obszarami AED.
- [ ] 1.2 Zbiór "Raport zbiorczy AED" ma zasoby CSV, GeoJSON i OSM (ODbL);
      zakładka Mapa pokazuje punkty.
- [ ] 1.3 API zwraca rekordy raportu: `https://api.mcod.local/1.4/resources/<id CSV>/data`.
- [ ] 1.4 Kreator: konto pełnomocnika Krosna, "Dodaj dane AED",
      plik Krosna, przypisanie kolumn, raport walidacji, publikacja.
- [ ] 1.5 Walidator "Sprawdź swój plik" pokazuje błędy pliku
      z błędami bez logowania.
- [ ] 1.6 Karta urządzenia i "Zgłoś problem" dla rekordu raportu i dla
      urządzenia demo: zgłoszenie bez imienia i kontaktu przechodzi, widzi
      je tylko dysponent urządzenia, e-mail w MailHog.
- [ ] 1.7 Strona akcji `/pl/aed`: liczniki i mapa pokrycia gmin,
      także na telefonie.
- [ ] 1.8 "Najbliższy AED" w zakładce PoCoTo.

Uwagi:

## 2. Prezentacja PDF

`submission/mapa-serc-prezentacja.pdf`

- [ ] 2.1 Treść slajdów zgodna z prototypem i opisem.
- [ ] 2.2 Zrzuty ekranu aktualne, w tym strona akcji z licznikami i mapą.
- [ ] 2.3 Załącznik A prezentacji: stan każdej zasady portalu (spełnione,
      częściowo, wymaga decyzji) i wynik automatycznej kontroli dostępności.
- [ ] 2.4 Rozmiar do 10 MB, co najmniej 5 slajdów.

Uwagi:

## 3. Księga znaku

`brand/ksiega-znaku-mapa-serc.pdf`

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

`submission/mapa-serc-demo.mp4` (1 min 42 s, bez dźwięku, z napisami)

- [ ] 6.1 Nagranie pokazuje kroki dysponenta i odbiorcy danych.
- [ ] 6.2 Długość do 2 minut; brak haseł i prywatnych danych na ekranie.

Uwagi:

## 7. Zgłoszenia AED: decyzje do potwierdzenia

- [ ] 7.1 Treść klauzuli RODO w formularzu "Zgłoś problem" (strona
      urządzenia `/pl/aed/<aed_id>`).
- [ ] 7.2 Okres przechowywania danych zgłaszającego: imię lub podpis
      i kontakt (oba opcjonalne) są usuwane 30 dni po oznaczeniu zgłoszenia
      jako rozwiązane.

Uwagi:
