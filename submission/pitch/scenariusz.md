# Mapa Serc - scenariusz wystąpienia (5 minut)

Wystąpienie zaczyna się od pokazu na żywo, nie od slajdów. Prezentacja PDF
i nagranie są planem awaryjnym. Założenie: 5 minut na wystąpienie; format
finału nie jest potwierdzony, więc niżej jest też wariant, w którym jury
samo wybiera przypadek użycia.

Wersję roboczą tego dokumentu przygotowało narzędzie AI (Claude Code) na
podstawie materiałów z repozytorium; autor wygłasza ją własnymi słowami.

## Jedno zdanie

Mapa Serc to mechanizm w kodzie portalu dane.gov.pl, dzięki któremu każda
instytucja publikuje dane o swoich defibrylatorach w jednym układzie,
a portal składa z nich jeden otwarty zbiór z mapą i API.

## Przebieg

| Czas | Część | Co pokazuję | Co mówię |
|---|---|---|---|
| 0:00-0:25 | Wejście | Strona akcji https://mcod.local/pl/aed, liczniki | "Gdy serce staje, liczy się każda minuta. Wolontariusze OpenStreetMap zaznaczyli w Polsce ponad 18 tysięcy AED. W dane.gov.pl dane do pobrania ma 74. Pokażę, jak to zmienić bez budowania nowego systemu." |
| 0:25-1:40 | Scenariusz 1: dysponent publikuje | Panel dostawcy, kreator "Dodaj dane AED" | Opis w sekcji niżej |
| 1:40-2:40 | Scenariusz 2: jeden zbiór, mapa i API | Zbiór "Raport zbiorczy AED", mapa zasobu, API | Opis w sekcji niżej |
| 2:40-3:40 | Scenariusz 3: kod QR i zgłoszenie | Karta urządzenia na telefonie, panel, e-mail | Opis w sekcji niżej |
| 3:40-4:15 | Mapa luk i akcja | Strona akcji: mapa, lista gmin, sekcja dla dysponentów | "Na pomarańczowo są 2124 gminy, w których wolontariusze zaznaczyli AED, a portal nie ma o nich danych. To gotowa lista urzędów do zaproszenia. Do nich akcja mówi wprost: lista AED w szufladzie nikogo nie uratuje." |
| 4:15-4:45 | Czego nie ma | Bez przełączania ekranu | "To prototyp na lokalnej kopii portalu. Żaden rekord nie potwierdza, że urządzenie działa. Dysponenci 74 rekordów z plików miast nie są potwierdzeni. Licencja punktów OpenStreetMap wymaga decyzji operatora. Wszystko to jest opisane w ograniczeniach." |
| 4:45-5:00 | Prośba | Slajd 14 albo strona repozytorium | "Do wdrożenia potrzeba decyzji operatora portalu, nie nowego systemu. Kod, dane, znak i nagranie są w jednym publicznym repozytorium. Dziękuję." |

Suma: 5 minut. Przy limicie 3 minut pomijam scenariusz 3 i skracam mapę
luk do jednego zdania.

## Scenariusz 1: dysponent publikuje dane (75 s)

Konto: `krosno.agent@mcod.local` (hasło w lokalnym `.env`, zmienna
`SEED_KROSNO_AGENT_PASSWORD`). Adres: https://admin.mcod.local/aed/kreator/

1. Wgrywam plik `backend/data/aed/sources/krosno/Defibrylator_jAmxQcp.csv`.
   Mówię: "To prawdziwy plik Krosna z dane.gov.pl, w układzie miasta."
2. Ekran "Kolumny": kreator sam przypisał szerokość, długość i nazwę.
   Wpisuję dysponenta "Urząd Miasta Krosna" i datę danych `2024-02-19`.
   Mówię: "Kreator nie zgaduje dysponenta ani daty. Gdy pliku ich nie ma,
   trzeba je podać."
3. Raport walidacji: 21 rekordów, plik przechodzi kontrolę, oznaczenie
   "Zgodny ze standardem AED".
4. Nie klikam "Opublikuj zasób". Mówię: "Po publikacji zasób trafia do
   zbioru instytucji, a raport zbiorczy uwzględnia go przy najbliższym
   odświeżeniu, codziennie o 03:30 UTC."

Jeśli jury chce zobaczyć błąd: publiczny walidator
https://admin.mcod.local/aed/sprawdz-plik/ i plik
`backend/data/aed/sources/marki/Defibrylator_GminaMiastoMarki_1.csv`
(cały wiersz w jednej komórce). Walidator pokazuje błędy bez logowania.

## Scenariusz 2: jeden zbiór, mapa i API (60 s)

1. Portal, zakładka Dane, zbiór "Raport zbiorczy AED": kategoria Zdrowie,
   częstotliwość "Codziennie", zasoby CSV i GeoJSON.
   Mówię: "86 rekordów w demo: 74 z plików czterech miast i 12 fikcyjnych,
   oznaczonych jako dane demonstracyjne."
2. Zasób CSV, zakładka Mapa: punkty na wbudowanej mapie portalu.
3. "Opcje mapy", "określ swoją lokalizację", adres "Legionowo, Rynek",
   promień 1 km, "Zastosuj filtr". Mówię: "To jest Najbliższy AED: ta sama
   mapa portalu z filtrem odległości." Wymaga internetu (publiczny geokoder
   Nominatim, z którego korzysta portal).
4. Karta z API: `https://api.mcod.local/1.4/resources/<id zasobu CSV>/data?per_page=1`.
   Mówię: "Każdy rekord ma wydawcę, datę pobrania, licencję i oznaczenia
   jakości. Twórca aplikacji nie potrzebuje niczego poza API portalu."

## Scenariusz 3: kod QR i zgłoszenie (60 s)

Okno przeglądarki zwężone do szerokości telefonu.

1. https://mcod.local/pl/aed/5b0c3c1e-6f0e-4a57-9d4e-2f1a3b7c8d01
   (fikcyjne urządzenie demo). Mówię: "Tak wygląda strona po zeskanowaniu
   kodu z naklejki. Taką stronę ma każdy rekord raportu."
2. "Zgłoś problem": wybieram "AED zamknięty lub niedostępny", wpisuję jedno
   zdanie, wysyłam bez imienia i kontaktu.
   Mówię: "Formularz nie wymaga danych osobowych i nie zastępuje numeru 112."
3. Drugie okno, konto `demo.agent@mcod.local`:
   https://admin.mcod.local/aed_reports/aedincidentreport/ - zgłoszenie
   widzi tylko instytucja odpowiedzialna za dane tego urządzenia.
4. http://localhost:8025/ - e-mail do tej instytucji (lokalna skrzynka
   testowa).

## Gdy jury wybiera przypadek użycia

| Prośba jury | Gdzie klikam | Czas |
|---|---|---|
| "Pokaż, jak urząd dodaje dane" | Scenariusz 1 | 75 s |
| "Co z plikiem z błędami?" | Publiczny walidator i plik Marek | 40 s |
| "Gdzie jest najbliższy AED?" | Scenariusz 2, krok 3 | 30 s |
| "Jak to pobrać maszynowo?" | Scenariusz 2, krok 4; metadane RDF: `https://api.mcod.local/catalog/dataset/<id zbioru>.rdf` | 30 s |
| "AED jest zamknięty, co robi świadek?" | Scenariusz 3; najpierw zdanie, że w nagłym przypadku dzwoni się pod 112 | 60 s |
| "Skąd wiadomo, gdzie brakuje danych?" | Strona akcji, mapa i tabela "Gminy z lukami" | 30 s |
| "Jak odróżnić dane prawdziwe od demo?" | Strona akcji: liczniki "w tym demonstracyjnych", fioletowe ramki na mapie | 20 s |
| "Pokaż znak i materiały" | Slajdy 11 i 12 PDF, `brand/ksiega-znaku-mapa-serc.pdf` | 30 s |

## Przygotowanie przed wejściem

Najpóźniej 30 minut wcześniej:

1. Uruchomić portal według `README.md`, sekcja "Uruchomienie od zera"
   (albo `docker compose up -d` na przygotowanej bazie). Jeśli
   https://mcod.local/ nie odpowiada po starcie usług, uruchomić ponownie
   `docker compose up -d nginx`.
2. Załadować urządzenia i wpis "Najbliższy AED": `load_aed_devices` (dwa
   pliki), `load_aed_report_devices`, `seed_aed_showcase` (README, sekcja
   "Zgłoszenia AED i kody QR").
3. Otworzyć raz każdą stronę z tego scenariusza. Pierwsze otwarcie trwa
   1-2 minuty, bo frontend kompiluje się przy pierwszym wejściu.
4. Sprawdzić stronę akcji: liczniki 8 / 4 / 86 / 4 z 2479 i mapa z lukami.
   Gdy mapa pokazuje 0 luk, wyczyścić cache API (README, "Cache API po
   `aed_refresh`").
5. Zalogować dwa konta w dwóch oknach: `krosno.agent@mcod.local` (kreator)
   i `demo.agent@mcod.local` (zgłoszenia). Hasła są w lokalnym `.env`;
   nie pokazywać tego pliku na ekranie.
6. Przygotować karty w kolejności: strona akcji, kreator, zbiór, mapa
   zasobu, API, karta urządzenia (wąskie okno), panel zgłoszeń, MailHog.
7. Powiększenie przeglądarki 125%, tryb pełnoekranowy, wyłączone
   powiadomienia.
8. Sprawdzić internet (filtr odległości). Bez internetu pominąć krok 3
   scenariusza 2 i pokazać slajd 9.

## Plan awaryjny

- Portal nie działa albo nie ma rzutnika z moim komputerem: nagranie
  `submission/mapa-serc-demo.mp4` (1 min 59 s) i trzy zdania o tym, czego
  w nim nie widać (ograniczenia, prośba do operatora).
- Jest tylko PDF: slajdy 4-9 w kolejności scenariuszy, potem 13 i 14.
- Brak czasu: jedno zdanie z początku tego dokumentu, scenariusz 1,
  prośba.

## Liczby, które padają

| Liczba | Znaczenie | Źródło |
|---|---|---|
| 18 298 | punkty AED w Polsce w OpenStreetMap | eksport OpenAEDMap z 21.11.2026 |
| 74 | AED z danymi do pobrania w dane.gov.pl (cztery miasta) | zbiory 3624, 4955, 4581, 40593 |
| 86 | rekordy raportu w demo (74 i 12 fikcyjnych) | Raport zbiorczy AED w lokalnej instancji |
| 2124 | gminy z AED w OSM i bez danych w dane.gov.pl | strona akcji |
| 4 z 2479 | gminy z oficjalnymi danymi | strona akcji |
| 44 / 15 | pola wzorcowego zakresu danych / wymagane | `aed-standard/schema.json` |
| 3-6% | spadek szans na przeżycie z każdą minutą bez defibrylacji | Wytyczne ERC 2025, wyd. polskie |
