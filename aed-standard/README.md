# Wzorcowy zakres danych AED

Profil PL 1.0.0 określa wspólny format publikacji danych AED przez dysponentów
na dane.gov.pl. To propozycja dla zadania HackNation, a nie obowiązujący
państwowy standard ani potwierdzony rejestr sprawnych urządzeń.

| Plik | Zastosowanie |
|---|---|
| [field-dictionary.xlsx](field-dictionary.xlsx) | Słownik 44 pól: polska etykieta, typ, wymagalność, format, przykład i opis |
| [schema.json](schema.json) | Table Schema 2.0: typy i ograniczenia oraz rozszerzenia profilu `x-*` |
| [template.csv](template.csv) | Pełny nagłówek 44 pól do wypełnienia; bez przykładowego rekordu |
| [example.csv](example.csv) | Poprawny, całkowicie fikcyjny rekord, pokazujący format każdego pola |
| [mappings.csv](mappings.csv) | Wszystkie 44 pola dla pięciu zbiorów miejskich i OSM |
| [mappings.md](mappings.md) | Źródła, zasady konwersji, potwierdzone braki i ograniczenia |
| [validate.py](validate.py) | Lokalna kontrola CSV, bez pobierania danych i bez zależności zewnętrznych |
| [tests/test_validate.py](tests/test_validate.py) | Testy publicznego CLI: poprawny przykład i typowe błędy |
| [tests/test_contract.py](tests/test_contract.py) | Zgodność słownika, schematu, nagłówków i mapowań |

## Przygotowanie publikacji

1. Skopiuj `template.csv`. Zachowaj nazwy maszynowe kolumn; ich polskie
   objaśnienia znajdują się w XLSX. Nie wpisuj objaśnień jako kolejnych
   nagłówków ani rekordów. Jeden wiersz opisuje jedno urządzenie.
2. Nadaj `aed_id` jako UUID raz, w ewidencji dysponenta. Zachowaj go po
   zmianie adresu lub przeniesieniu AED. Nie używaj numeru wiersza, adresu
   ani hasha współrzędnych. Utrzymuj powiązanie identyfikatorów źródeł z tym
   UUID. Późniejsze zgłoszenie awarii wskazuje ten sam `aed_id` i dysponenta.
   W tym pliku nie przechowuj incydentów, danych pacjentów ani zgłaszających.
3. Uzupełnij wszystkie pola wymagane. `operator_name` to potwierdzona
   instytucja odpowiedzialna za AED i obsługę zgłoszeń. Nazwa obiektu,
   wydawca katalogu ani autor wpisu OSM nie stanowią takiego potwierdzenia.
   Nieznanego dysponenta trzeba ustalić przed przyjęciem rekordu.
   Publikacja dysponenta (`source_id` zaczyna się od `dysponent:`) zawsze
   wskazuje potwierdzonego dysponenta; walidator odrzuca w niej wartość
   `nieustalony` i flagę `operator_unconfirmed`. Wyjątek dotyczy wyłącznie
   raportu zbiorczego ze źródeł zewnętrznych: rekord bez potwierdzonego
   dysponenta ma `operator_name` = `nieustalony`, flagę
   `operator_unconfirmed`, a wydawcę danych źródłowych w
   `source_records[].publisher_name`. Opcjonalny `operator_regon` (9 lub 14
   cyfr z cyfrą kontrolną GUS) jednoznacznie identyfikuje dysponenta.
4. Nieznane wartości opcjonalne pozostaw puste. `unknown` jest dozwolone
   tylko w określonych słownikach; nie oznacza `false`, `working` ani `24/7`.
   Jeśli opcjonalna lub warunkowa kolumna jest pusta we wszystkich rekordach,
   usuń ją z publikowanego pliku, zachowując kolejność pozostałych kolumn.
   `fieldsMatch: superset` pozwala na taką projekcję. Pola wymagane muszą
   pozostać, a warunki między polami nadal obowiązują.
5. Zapisz UTF-8 bez BOM, separator przecinek, jeden nagłówek, końce wierszy
   CRLF, bez pustych wierszy. Używaj kropki dziesiętnej. Cudzysłowy, przecinki
   i końce linii wewnątrz komórek cytuj zgodnie z CSV (RFC 4180). Tablice
   `source_records` i `quality_flags` są tekstem JSON w cytowanej komórce CSV.
6. Uruchom walidator. Uzupełnij również wymagane metadane zbioru i zasobu
   w portalu: opis, instytucję, kategorię, słowa kluczowe, częstotliwość,
   warunki ponownego wykorzystania oraz datę danych. Ten schemat rekordów
   nie zastępuje metadanych portalu ani procedury przyjęcia publikacji.

```sh
python3 -B aed-standard/validate.py aed-standard/example.csv
python3 -B aed-standard/validate.py --template aed-standard/template.csv
python3 -B -m unittest discover -s aed-standard/tests -v
```

Python 3.10 lub nowszy. Kod 0 oznacza przejście opisanych kontroli, 1 błędy
danych, 2 błędne argumenty CLI. Domyślnie sam nagłówek nie jest poprawnym
zbiorem; `--template` sprawdza pełny nagłówek bez rekordów.

## Współrzędne i mapa portalu

`latitude` i `longitude` to liczbowe WGS84 w stopniach dziesiętnych.
Występują razem; dla `location_kind=fixed` obie wartości są wymagane.
Mobilnego AED bez aktualnej pozycji nie umieszczaj pod adresem siedziby
dysponenta. W publikacji obejmującej tylko takie urządzenia pomiń puste
kolumny współrzędnych. Do mapy przygotuj zasób z rekordami mającymi pozycję.

Po walidacji tabeli w panelu dostawcy, w zakładce map i wykresów przypisz:

| Kolumna CSV | Rola mapy |
|---|---|
| `longitude` | `l` (długość geograficzna) |
| `latitude` | `b` (szerokość geograficzna) |
| `name` | `label` (etykieta) |

Zapisz konfigurację i poczekaj na indeksowanie. Samo nazwanie kolumn nie
konfiguruje mapy automatycznie. Komplet `b`, `l`, `label` i numeryczny typ
współrzędnych wynikają z kodu portalu (MapsJSONField i TabularData).
Ten pakiet nie wykonuje publikacji ani testu mapy w działającym portalu.

Walidator sprawdza zakresy geograficzne oraz orientacyjną ramkę Polski:
48.9..55.1 N, 14..24.2 E. To kontrola pomyłek osi i oczywistych odległych
punktów, bez granic administracyjnych. Nie wykryje punktu Krosna opisanego
jako Marki. Sprawdź również zgodność z miejscowością i dokładną pozycją AED.

## Wymagalność i daty

`R` w schemacie oznacza wymagane, `O` opcjonalne, `C` warunkowe. XLSX używa
pełnych polskich nazw. `latitude` i `longitude` są warunkowe dla stałego
punktu i zawsze występują parami. `timezone=Europe/Warsaw` jest wymagane,
gdy podano `opening_hours`.

Daty kalendarzowe mają format `YYYY-MM-DD`, znaczniki czasu
`YYYY-MM-DDTHH:MM:SSZ` w UTC. `last_verified_at` dopuszcza datę lub pełny
znacznik UTC, aby nie dopisywać godziny do źródła podającego tylko dzień.

- `updated_at`: ostatnia zmiana treści rekordu, wymagana w każdym rekordzie.
- `retrieved_at`: udane pobranie danych; nie jest datą kontroli AED.
- `source_records[].source_data_date`: dzień, którego dotyczy źródłowy zasób.
- `source_records[].source_updated_at`: zmiana źródła, jeśli znana.
- `last_verified_at`: faktyczna weryfikacja, z osobną `verification_method`.
- `last_maintenance_on`: przegląd urządzenia; nie zastępuje go edycja mapy.

Godziny zapisuj w notacji [OSM opening_hours](https://wiki.openstreetmap.org/wiki/Key:opening_hours).
Mały walidator sprawdza obecność strefy, ale nie parsuje pełnej gramatyki OSM
ani nie oblicza dostępności. Przed takim obliczeniem użyj pełnego parsera OSM,
uwzględniającego święta i sezonowość. Nieprzeanalizowany opis zachowaj
w `opening_hours_raw`; samo umieszczenie na zewnątrz nie oznacza 24/7.

## Pochodzenie i licencje

Każdy rekord zawiera niepustą tablicę `source_records`. Każdy jej obiekt ma
wymagane tekstowe `source_id`, `source_record_id`, `source_url`, `retrieved_at`
oraz `license_url`. Dwa URL-e muszą być HTTP(S), bez danych logowania.
Przykład struktury JSON przed cytowaniem go w CSV:

```json
[{"source_id":"example:institution","source_record_id":"AED-001","source_url":"https://example.org/aed/AED-001","retrieved_at":"2026-11-21T13:42:00Z","license_url":"https://creativecommons.org/publicdomain/zero/1.0/"}]
```

Dodatkowe pola: `source_data_date`, `source_updated_at`, `attribution`,
`source_version`, `original_values`, `field_provenance`. Przy sprzecznych
źródłach w `field_provenance` zapisz dla nazwy pola wybrane source_id
i source_record_id oraz powód decyzji. To opis pochodzenia, nie mechanizm
scalania w tym pakiecie. Zachowaj oryginały i decyzje bez danych osobowych.

Ustal licencję źródła przed eksportem; brak linku blokuje rekord.
Prawdziwość linku, uprawnienie do publikacji i obowiązki licencji wymagają
osobnego sprawdzenia. CC BY wymaga atrybucji i oznaczenia zmian. Pochodna
baza z istotnego zakresu OSM podlega ODbL; nie staje się CC0 ani CC BY przez
konwersję do CSV. Zachowaj informację „© OpenStreetMap contributors”
i [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Obecny selektor
licencji XML portalu nie zawiera ODbL; sposób publikacji trzeba uzgodnić,
zanim obieca się taki eksport. Mapowanie tagów nie nadaje nowej licencji.

`example.csv` jest syntetyczny i nie zawiera rekordów OSM. Można go używać
jako przykładu na warunkach CC0 1.0 wskazanych w jego pochodzeniu.
Jego nazwy, kontakt, wyposażenie i współrzędne nie wskazują sprawdzonego AED.
Kody TERYT ilustrują format i nie potwierdzają zgodności z fikcyjnym adresem.

## Prywatność i granice kontroli

Publikuj tylko zatwierdzone kontakty instytucjonalne lub funkcyjne.
Nie publikuj nazwisk, imiennych e-maili, prywatnych telefonów, autora edycji
OSM, danych zgłaszającego, pacjenta ani kodów dostępu. Przejrzyj także wolny
tekst oraz oryginały źródłowe. Publiczne pochodzenie kontaktu nie jest
automatycznie podstawą jego ponownej publikacji.

Walidator wykrywa błędy struktury, typów, wymaganych danych i opisanych reguł
między polami. Nie dowodzi braku danych osobowych w dowolnym tekście,
legalności przetwarzania, istnienia instytucji/urządzenia, prawa do licencji,
dostępności kontaktu, poprawności godzin, istnienia kodu w TERYT ani sprawności
AED. `quality_flags=[]` nie jest certyfikatem jakości. Wspólny adres lub
współrzędne nie dowodzą, że dwa rekordy opisują to samo urządzenie.

## Podstawa i użycie AI

Propozycja zachowuje 43 pola z badań do zadania i dodaje opcjonalny `operator_regon` (2026-11-22); wzmacnia wymagalność
dysponenta i licencji dla każdego źródła. Podstawy: [standard techniczny
dane.gov.pl (2020)](https://dane.gov.pl/media/ckeditor/2020/06/16/standard-techniczny.pdf),
[Table Schema 2.0](https://datapackage.org/standard/table-schema/)
([źródło specyfikacji](https://github.com/frictionlessdata/specs/blob/main/content/docs/standard/table-schema.mdx)),
[tagi AED OSM](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator),
[TERYT](https://eteryt.stat.gov.pl/) i źródła wskazane w `mappings.md`.

AI wykorzystano do opracowania schematu, słownika, dokumentacji, mapowań,
danych syntetycznych oraz kodu walidatora i testów tego pakietu. Wykonano
kontrole automatyczne i niezależny przegląd; nie przeprowadzono oględzin AED
ani potwierdzenia danych przez dysponentów. To oświadczenie dotyczy pakietu;
materiały zgłoszeniowe muszą uwzględnić również użycie AI w pozostałych częściach projektu.
