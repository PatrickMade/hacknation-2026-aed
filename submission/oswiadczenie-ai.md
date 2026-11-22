# Oświadczenie o zakresie wykorzystania sztucznej inteligencji

Podstawa: regulamin zadania "Misja AED - Dane na ratunek", par. 2 ust. 8
("Zespół zobowiązany jest wskazać w rozwiązaniu zakres wykorzystania
sztucznej inteligencji (AI) przy opracowywaniu rozwiązania").

Rozwiązanie przygotowałem jako zespół jednoosobowy, z intensywnym użyciem
narzędzi AI we wszystkich obszarach pracy. Poniżej opisuję, do czego AI
zostało użyte, a co jest decyzją i pracą człowieka.

## Narzędzia

- **Claude Code** (Anthropic), modele Claude Opus 5.5 (analiza, kod,
  dokumentacja, teksty, przeglądy) i Claude Fable 5.2 (marka i materiały
  wizualne, slajdy, nagranie demo, końcowe teksty zgłoszenia i ich
  przeglądy).
- **Codex** (OpenAI), model GPT-6.1 Sol (część analiz, przygotowanie
  wzorcowego zakresu danych, pierwsza wersja lokalnego uruchomienia portalu).
- Wyszukiwarka internetowa dla agentów AI (Exa) do wyszukiwania źródeł
  w researchu.

Agenci AI pracują w osobnych zadaniach, każde na własnej gałęzi. Po
utworzeniu szkieletu repozytorium zmiany trafiają do niego przez pull
requesty z automatycznymi kontrolami (analiza statyczna, testy, kontrola
konfiguracji) i przeglądem w osobnej sesji AI.

## Zakres użycia AI według obszarów

| Obszar | Co wykonało AI | Co wykonał lub zdecydował człowiek |
|---|---|---|
| Analiza zadania i research | Odczyt treści zadania, regulaminów i przewodnika uczestnika; analiza zasad i API dane.gov.pl, istniejących zbiorów AED i kodu portalu; notatki badawcze ze źródłami | Wybór kierunku po rozmowach z mentorami; akceptacja planu rozwiązania; rozstrzygnięcie pytań otwartych |
| Architektura | Propozycje wariantów i punktów rozszerzenia portalu | Decyzja: moduł AED wewnątrz lokalnej instancji portalu dane.gov.pl, bez zmiany jego wyglądu; raport zbiorczy na wzór zbioru 4354; OSM jako osobny zbiór na ODbL; jury uruchamia prototyp lokalnie |
| Zbieranie danych | Skrypty pobierające wpisy o AED ze stron gov.pl i BIP (739 wpisów z 20 źródeł) oraz pobranie migawek pięciu zbiorów z dane.gov.pl | Decyzja, że wpisy ze stron urzędów nie wchodzą do raportu, bo nie mają rozstrzygniętej licencji |
| Wzorcowy zakres danych (`aed-standard/`) | Słownik 44 pól (XLSX), schemat Table Schema, szablon i przykład CSV, mapowania źródeł, walidator i testy, dokumentacja | Przyjęcie zakresu i zasad (dysponent jako odpowiedzialny, brak danych osobowych, licencja każdego źródła) |
| Uruchomienie portalu | Konfiguracja lokalnego uruchomienia, dane startowe z kontami, dokumentacja uruchomienia | Kod portalu dane.gov.pl to oficjalny kod jego autorów (GPLv3), nie wygenerowany przez AI; zmiany lokalne opisuje `UPSTREAM.md` |
| Raport zbiorczy AED (agregator) | Moduł `backend/mcod/aed_aggregate` (mapowanie pięciu zbiorów do standardu, walidacja, deduplikacja, pochodzenie rekordów, publikacja zasobów raportu), komenda `aed_refresh`, testy | Zakres funkcji; akceptacja działania w demo według `akceptacja.md` [do wykonania] |
| Kreator dysponenta i walidator | Moduł `backend/mcod/aed_wizard` (kreator "Dodaj dane AED", publiczny walidator), testy | Zakres funkcji; akceptacja działania w demo według `akceptacja.md` [do wykonania] |
| Zgłoszenia AED | Moduł `backend/mcod/aed_reports` (rejestr urządzeń po `aed_id`, API zgłoszeń ze zgodą RODO, panel dysponenta, e-mail, własny koder QR sprawdzony bit po bicie z biblioteką referencyjną qrcodegen), strona `/pl/aed/<aed_id>`, testy i fikcyjne dane demo; także treść klauzuli o przetwarzaniu danych w formularzu (wzór czekający na weryfikację prawną) i mechanizm usuwania danych zgłaszającego 30 dni po rozwiązaniu zgłoszenia | Zakres funkcji; akceptacja działania w demo według `akceptacja.md` [do wykonania] |
| Strona akcji i "Najbliższy AED" | Strona akcji z licznikami i mapą pokrycia gmin, wpis "Najbliższy AED" w zakładce PoCoTo | Zakres funkcji; akceptacja działania w demo według `akceptacja.md` [do wykonania] |
| Nazwa, hasło, logo, księga znaku (`brand/`) | Kilka rund propozycji nazw i haseł oraz szkiców znaku; finalne pliki znaku i naklejki z kodem QR zapisane jako SVG; eksport do PNG, JPG i PDF w przeglądarce Google Chrome i w programie ImageMagick; księga znaku. Model: Claude Fable 5.2. Kontur Polski pochodzi z danych Natural Earth (domena publiczna), a krój Figtree jest na licencji SIL Open Font License 1.1 | Wybór nazwy "Mapa Serc"; własne sformułowanie hasła "Wszystkie AED pod ręką."; odrzucenie wcześniejszych propozycji i wybór wariantu znaku; akceptacja finalnych plików |
| Teksty zgłoszenia i prezentacja | Wersje robocze opisu, listy ograniczeń, slajdów (HTML) i tego oświadczenia; zrzuty ekranu i nagranie demo (`mapa-serc-demo.mp4`) przygotowane skryptem przeglądarki z lokalnej instancji portalu; okładka HackTribe | Redakcja i akceptacja treści; wygłoszenie prezentacji |
| Kontrola jakości | Testy automatyczne i przeglądy kodu oraz treści w osobnych sesjach AI; kontrola modułów AED w przeglądarce; automatyczna kontrola dostępności nowych stron (axe-core) | Przegląd końcowy materiałów przed wysłaniem [do wykonania] i odpowiedzialność za całość |

## Czego AI nie robiło

- Nie wytworzyło danych o rzeczywistych urządzeniach. Rekordy AED pochodzą
  z opisanych źródeł z adresem i datą pobrania. Rekord przykładowy
  w `aed-standard/example.csv` jest w całości fikcyjny i tak oznaczony.
- Nie publikowało niczego w produkcyjnym portalu dane.gov.pl ani nie
  kontaktowało się z dysponentami czy instytucjami.
- Nie potwierdzało fizycznie istnienia ani sprawności żadnego AED.

## Odpowiedzialność

Ostateczny kształt rozwiązania jest efektem mojej analizy i decyzji.
Przed wysłaniem zgłoszenia przeglądam wszystkie materiały w całości i biorę
za nie odpowiedzialność jako autor.
