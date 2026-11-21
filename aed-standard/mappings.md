# Mapowania źródeł AED

[mappings.csv](mappings.csv) zawiera 43 wiersze, po jednym dla każdego pola
profilu, i sześć kolumn źródeł. To instrukcja mapowania, nie wykonany import.
`BRAK` oznacza brak w sprawdzonym źródle, `NADAJ` czynność dysponenta,
`POTWIERDŹ` warunek przyjęcia. Żaden brak nie upoważnia do zgadywania.
Wszystkie pola Warszawy mają status `NIEPOTWIERDZONE`, bo rzeczywistego
payloadu AED nie uzyskano. Mapowanie tego źródła jest świadomie otwartym
kontraktem do uzupełnienia, a nie twierdzeniem o obsługiwanym importerze.

## Źródła i dowody

| Źródło | Zasób | Potwierdzenie i ograniczenie |
|---|---|---|
| [Krosno 3624](https://api.dane.gov.pl/1.4/datasets/3624) | [K1: CSV](https://api.dane.gov.pl/media/resources/20240219/Defibrylator_jAmxQcp.csv), resource 54632 | Sześć nagłówków potwierdzonych odczytem 2026-11-21 UTC |
| [Marki 4955](https://api.dane.gov.pl/1.4/datasets/4955) | [M1: CSV](https://api.dane.gov.pl/media/resources/20250710/Defibrylator_GminaMiastoMarki_1.csv), resource 68355 | Jedna zewnętrzna kolumna CSV, zawierająca wewnętrzny rekord; odczyt 2026-11-21 UTC |
| [Przemyśl 4581](https://api.dane.gov.pl/1.4/datasets/4581) | [P1: GeoJSON](https://przemysl.skycms.com.pl/open-data/20/1730818801_b50R6UVxPgoVdBbq/geojson), [P2: kopia portalu](https://api.dane.gov.pl/media/resources/20241106/1730818801_b50R6UVxPgoVdBbq.geojson) | Klucze properties i geometry potwierdzone w P2 2026-11-21 UTC; różne formaty jednego zbioru nie są dodatkowymi urządzeniami |
| [Warszawa 39512](https://api.dane.gov.pl/1.4/datasets/39512) | [Katalog miejski](https://dane.um.warszawa.pl/pl/catalogue/7bc32ffc-c2ac-4d32-83c9-b6f7a0b38de8) | Potwierdzone metadane katalogu, nie schemat rekordów; oznaczenie JSON nie dowodzi działającego eksportu AED |
| [Legionowo 40593](https://api.dane.gov.pl/1.4/datasets/40593) | [L1: CSV](https://api.dane.gov.pl/media/resources/20260914/aed.csv), [resource 2625221](https://api.dane.gov.pl/1.4/resources/2625221) | Jedenaście nagłówków potwierdzonych odczytem 2026-11-21 UTC |
| [OSM AED tags](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator) | [OpenAEDMap PL GeoJSON](https://openaedmap.org/api/v1/countries/PL.geojson) lub Overpass emergency=defibrillator | Mapowanie tagów według dokumentacji i dostarczonych badań; pakiet nie pobiera krajowej bazy ani nie potwierdza kompletności |

Nazwy plików i data pobrania nie są dowodem aktualności pojedynczego AED.
Przed realnym eksportem odczytaj metadane zasobu i warunki wykorzystania;
nie wpisuj licencji zbiorczej na podstawie samej domeny dane.gov.pl.

## Reguły odczytu

- Krosno i Marki mają nagłówki `Długość geograficzna`, `Szerokość geograficzna`,
  ` Nazwa`, ` Lokalizacja`, ` Adres`, ` Numer Id`. Początkowe spacje należą
  do zaobserwowanych nagłówków; usuń je przy dopasowaniu nazw, a nie z
  identyfikatorów. `Numer Id` przechowuj w przestrzeni danego źródła.
  Nie udowodniono trwałości tego klucza pomiędzy wszystkimi wydaniami.
- W Marki najpierw odczytaj CSV, potem wewnętrzny rekord z jedynej komórki.
  Zachowaj obie reprezentacje do kontroli. Większość wierszy zawiera wartości
  około 52.x,21.x mimo nagłówka długość/szerokość. Rekord szkoły nr 5 ma parę
  21.72034402175176,49.718809346153336 identyczną z pierwszą parą Krosna
  według badań. Nie naprawiaj całego pliku zamianą osi. Kontrola gminy i
  indywidualne rozstrzygnięcie muszą poprzedzić publikację.
- GeoJSON Przemyśla: `geometry.coordinates=[longitude,latitude]` dla Point.
  Właściwości mają m.in. `id`, `name`, `description`, `city`, `street`,
  `home_number`, `postcode`, `phone`, `email`. Ogólne objaśnienie AED
  w `description` nie staje się opisem drogi do szafki. Telefon i e-mail
  są kandydatami do oceny prywatności, bez automatycznej publikacji.
- Legionowo: `nazwa`, `cecha_ulicy`, `nazwa_ulicy`, `nr_budynku`, `nr_lokalu`,
  `kod_pocztowy`, `miejscowosc`, `kod_terc`, `kod_simc`,
  `szerokosc_geograficzna`, `dlugosc_geograficzna`. Zachowuj tekstowe kody.
  Niepełny sześciocyfrowy TERC uzupełnia się z datowanego rejestru,
  bez arbitralnego dopisywania cyfry. Wspólne pozycje policji i straży
  miejskiej są kandydatami do kontroli, bez automatycznego scalenia.
- Portalowe tabele API `col1`, `col2` mapuj przez `meta.headers_map`.
  Dla identyfikatorów używaj `repr`: `0920806` nie może stać się `920806.0`.
  Marki nadal zwraca jedną zakodowaną kolumnę, więc tabela API nie naprawia pliku.
- OSM: filtr `emergency=defibrillator`; identyfikator `node/123`, `way/123`
  i `relation/123` to różne obiekty. Zapisz typ i ID, wersję oddzielnie.
  Współrzędne środka way/relation są przybliżeniem, nie pomiarem szafki.
  `access=emergency` jest przestarzałe; nie oznacza automatycznie public.
  `check_date`, `survey:date` wymagają oceny znaczenia. Czas edycji i autor
  edycji nie są datą kontroli i dysponentem.

## Warunki przyjęcia

Pochodzenie musi wskazywać URL konkretnej reprezentacji, lokalny klucz
rekordu, czas pobrania i licencję. `source_id` opisuje ciągłość zbioru,
a wersja/ID zasobu pozwala odtworzyć konkretny odczyt. Gdy brak trwałego
klucza, nadaj go raz i utrzymuj rejestr powiązań; adres i numer wiersza
mogą służyć do ręcznego wyszukania, ale nie są trwałą tożsamością AED.

Brak potwierdzonego dysponenta lub licencji zatrzymuje eksport. To celowe:
istniejące źródła nie muszą samodzielnie spełniać pełnego profilu.
Przechowuj je do wyjaśnienia zamiast przedstawiać niepełne rekordy jako
gotowe do publikacji. Źródła miejskie zwykle nie dowodzą sprawności,
godzin ani zasad dostępu; używaj `unknown`, jeśli słownik je dopuszcza.

Nie przepisuj osób, prywatnych kontaktów, danych autora OSM ani informacji
medycznych do pochodzenia. Nie łącz istotnego zakresu OSM z CC0 bez
uwzględnienia ODbL. Szczegóły licencji i ograniczenia kontroli: [README](README.md).
