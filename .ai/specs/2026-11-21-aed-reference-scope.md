# Wzorcowy zakres danych AED

Issue: APP-41
Source doc: .ai/specs/2026-11-21-aed-reference-scope.md
Route: agreed delivery

## TLDR

Dysponenci potrzebują wspólnego formatu publikacji AED na dane.gov.pl.
Repozytorium nie zawiera obecnie tego kontraktu. Pakiet `aed-standard/`
dostarczy słownik XLSX, szablon, schemat Table Schema, przykład, mapowania
źródeł i lokalny walidator z testami.

## Scope

Punkt wyjścia: 43 pola propozycji badawczej, zasady publikacji CSV i pułapki
źródeł. Zmiany obejmują wyłącznie `aed-standard/` oraz tę specyfikację,
która zawiera również plan wykonania. Poza zakresem: portal, Flutter,
agregacja, branding, publikacja w serwisie i kontakt z dysponentami.

## Acceptance

1. `field-dictionary.xlsx` zawiera dokładnie 43 pola, polskie etykiety, typ,
   wymagalność, format/wartości, przykład i opis. Odczyt XLSX i porównanie z
   `schema.json` dowodzą zgodności nazw, kolejności i wymagalności.
2. `template.csv` ma jeden nagłówek wszystkich 43 pól i nie zawiera rekordów.
   `example.csv` zawiera fikcyjne dane, przechodzi CLI walidatora i nie ma
   całkowicie pustych kolumn. Pliki używają UTF-8, przecinka, CRLF i ISO 8601.
3. `schema.json` jest Table Schema: pola, typy, constraints, primaryKey,
   missingValues. Dodatkowe reguły między polami są jawnie opisane w README
   i walidatorze; sam ogólny czytnik Table Schema nie dowodzi ich spełnienia.
4. `mappings.csv` zawiera po jednym wierszu na każde z 43 pól i kolumny
   dla Krosna 3624, Marki 4955, Przemyśla 4581, Warszawy 39512,
   Legionowa 40593 oraz OSM. `mappings.md` podaje źródła i reguły konwersji,
   braków i odrzucenia. Warszawa ma status niepotwierdzonego payloadu,
   bez wymyślonych nazw pól. To mapowania projektowe, nie importery.
5. `validate.py` i testy sprawdzają strukturę CSV, required/optional,
   słowniki, typy, zakresy, skończone liczby, daty, identyfikatory TERYT,
   unikalność aed_id, współrzędne parami i obecność dla fixed, timezone
   przy opening_hours, odpowiedzialnego dysponenta i pochodzenie z licencją.
   Typowe błędy mają niezerowy kod wyjścia i komunikat z polem/wierszem.
6. README opisuje stabilność identyfikatorów, puste wartości, prywatność,
   projekcję pustych kolumn, ustawienia mapy `longitude -> l`,
   `latitude -> b`, `name -> label`, daty, licencjonowanie i granice walidacji.
   Zawiera ujawnienie zakresu użycia AI dla tego pakietu.
7. Wymagane kontrole repozytorium, testy pakietu i niezależny przegląd
   przechodzą przed merge gate. Diff nie dotyka innych powierzchni.

## Contract decisions

- Zachowujemy nazwy wszystkich 43 pól badawczych. `operator_name` jest
  wymagany dla przyjętego rekordu, bo wskazuje odpowiedzialnego dysponenta.
  Brak potwierdzonej instytucji zatrzymuje publikację; wydawca katalogu ani
  właściciel budynku nie staje się automatycznie dysponentem.
- `source_records` jest tablicą JSON w komórce CSV. Każdy element wymaga
  source_id, source_record_id, source_url, retrieved_at, license_url.
  Jest to wzmocnienie propozycji: brak ustalonej licencji blokuje eksport.
  `updated_at` jest wymaganą datą zmiany treści rekordu, a source_data_date,
  source_updated_at i last_verified_at zachowują odrębne znaczenie.
- aed_id to UUID dysponenta, niezależny od lokalizacji i numeru wiersza,
  niezmienny przy przeniesieniu AED. Powiązanie incydentu używa tego ID;
  ten pakiet nie zbiera zgłoszeń ani danych pacjentów.
- Opcjonalne kolumny można pominąć w publikowanym CSV, zachowując kolejność
  schematu. Wymagane kolumny pozostają; warunkowe są wymagane, gdy zachodzi
  ich warunek (fixed lub opening_hours). Walidator
  odrzuca całkowicie puste kolumny w pliku z rekordami; szablon jest
  wyłącznie nagłówkiem i wymaga osobnego trybu `--template`.
- Godziny pozostają w notacji OSM, bez nowej notacji własnej. Mały walidator
  nie interpretuje pełnej gramatyki opening_hours; wymaga strefy czasowej.
  Nieprzeanalizowany tekst trafia do opening_hours_raw. Dokumentacja wymaga
  pełnego parsera OSM przed użyciem harmonogramu do obliczania dostępności.
- Dane przykładowe są fikcyjne, z kontaktem funkcyjnym example.org, bez
  numerów prywatnych i bez skopiowanych rekordów OSM. Przykłady formatów
  TERYT nie potwierdzają istnienia jednostek w bieżącym rejestrze.

## Safety and limits

Bezpieczeństwo zależy od odrzucenia rekordów bez dysponenta/licencji oraz
od zachowania nieznanego stanu zamiast fałszywych współrzędnych czy 24/7.
Testy negatywne sprawdzają te granice. Walidator nie dowodzi prawa do danych,
braku danych osobowych w dowolnym tekście, zgodności licencji, istnienia AED,
dokładności lokalizacji, przynależności do gminy ani aktualności TERYT.
Polska ramka współrzędnych jest testem orientacyjnym, nie granicą kraju.
Marki wymaga kontroli każdego rekordu; powielenie współrzędnych Krosna nie
jest naprawiane zamianą osi. Nie scalaj urządzeń po samym adresie.
ODbL dla pochodnych danych OSM nie znika po konwersji ani wpisaniu CC0
na poziomie pliku. Publikacja i portalowy wybór licencji pozostają poza zakresem.

## Delta

ADDED: WHEN dysponent przygotuje CSV, THEN może sprawdzić lokalnie jego
strukturę i wymagane dane, uzyskując kod 0 lub listę błędów z kodem 1.
ADDED: WHEN mapowane jest starsze źródło, THEN słownik i mapowania określają
pola oraz jawne braki wymagające potwierdzenia przed publikacją.

## Verification and progress

Specyfikacja zawiera plan, aby zachować ograniczenie zmian do pakietu i specu.
To jeden kontrakt publikacji: słownik, serializacja i walidator służą temu
samemu formatowi. Nie dodajemy samodzielnej usługi ani agregatora.

### Phase 1: Kontrakt i dane

- [x] 1.1 Zapisać schemat, słownik XLSX, szablon i fikcyjny przykład. - bb5906c8c18178bf133e0313cbe3457895b1bae5
- [x] 1.2 Opisać sześć mapowań i instrukcję publikacji. - bb5906c8c18178bf133e0313cbe3457895b1bae5

### Phase 2: Walidacja i dostarczenie

- [x] 2.1 Wykazać RED/GREEN dla walidatora przez publiczne CLI. - bb5906c8c18178bf133e0313cbe3457895b1bae5
- [x] 2.2 Uruchomić testy pakietu i skonfigurowane bramki projektu. - bb5906c8c18178bf133e0313cbe3457895b1bae5
- [ ] 2.3 Uzyskać niezależny przegląd i scalić PR przez merge gate.

Testy: `python3 -B -m unittest discover -s aed-standard/tests -v`;
`python3 -B aed-standard/validate.py aed-standard/example.csv`;
`python3 -B aed-standard/validate.py --template aed-standard/template.csv`.
Pełna bramka w kolejności z `.ai/agentic.config.json`. Brak zmiany aplikacji
oznacza brak nowych scenariuszy urządzeń; właściciel nie uruchamia urządzeń.

## Evidence

Badania dostarczone z zadaniem: sekcje 2, 4, 5 research-aed.md.
Bezpośredni odczyt nagłówków Krosna, Marki i Legionowa oraz kluczy GeoJSON
Przemyśla 2026-11-21 UTC potwierdził opisane mapowania. Kod portalu
MapsJSONField i TabularData potwierdził komplet `b`, `l`, `label`.
Linki publiczne i statusy potwierdzenia znajdą się w pakiecie.

Weryfikacja 2026-11-21 UTC na treści bb5906c8c18178bf133e0313cbe3457895b1bae5:

- RED: `python3 -B -m unittest discover -s aed-standard/tests -v`, kod 1:
  test_example_passes, `AssertionError: 1 != 0`, CLI informuje o braku
  implementacji. Po dodaniu obsługi CSV i typów: kod 0, jeden test.
- Drugi RED: zamienione osie i źródło bez license_url kończyły się kodem 0,
  a test oczekiwał 1. Dodano reguły między polami i kontrolę pochodzenia.
- GREEN końcowy: ten sam unittest, kod 0, 10 metod z przypadkami błędów;
  oba jawne wywołania CLI dla przykładu i szablonu: kod 0.
- `fvm flutter analyze`: kod 0, No issues found.
- `fvm flutter test`: kod 0, 1 test, All tests passed.
- `python3 -B .ai/scripts/check_project_copy.py`: kod 0, passed.
- `python3 -B .ai/scripts/check_client_config.py`: kod 0, passed.
- `gitleaks dir aed-standard --redact --no-banner` i analogiczna kontrola
  specyfikacji: kod 0, no leaks found.
- XLSX sprawdzono strukturalnie: 43 wiersze pól, komplet siedmiu kolumn,
  zgodność z JSON, brak formuł i błędów komórek. Nie testowano renderowania
  w Excelu ani publikacji plików w działającym portalu.

Przegląd spójności zakresu w niezależnym kontekście nie znalazł problemów.
Pełny przegląd PR i merge pozostają krokiem 2.3; wynik zostanie zapisany
w rekordzie przeglądu i zadaniu, ponieważ scalenie jest czynnością końcową.
