# Oświadczenie o zakresie wykorzystania sztucznej inteligencji

Podstawa: regulamin zadania "Misja AED - Dane na ratunek", par. 2 ust. 8
("Zespół zobowiązany jest wskazać w rozwiązaniu zakres wykorzystania
sztucznej inteligencji (AI) przy opracowywaniu rozwiązania").

Rozwiązanie przygotowałem jako zespół jednoosobowy, z intensywnym użyciem
narzędzi AI we wszystkich obszarach pracy. Poniżej opisuję, do czego AI
zostało użyte, a co jest decyzją i pracą człowieka.

## Narzędzia

- **Claude Code** (Anthropic), modele Claude Opus 5.5 (analiza, kod,
  dokumentacja, teksty, przeglądy) i Claude Fable 5.2 (kierunki marki
  i materiały wizualne).
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
| Architektura | Propozycje wariantów i punktów rozszerzenia portalu | Decyzja: moduł AED wewnątrz lokalnej instancji portalu dane.gov.pl, bez zmiany jego wyglądu; raport zbiorczy na wzór zbioru 4354; OSM jako osobny zasób na ODbL; jury uruchamia prototyp lokalnie |
| Zbieranie danych | Skrypty pobierające wpisy o AED ze stron gov.pl i BIP (739 wpisów z 20 źródeł) oraz pobranie migawek pięciu zbiorów z dane.gov.pl | Decyzja, że dane ze stron urzędów służą tylko jako oznaczone dane demonstracyjne, a nie jako dane urzędowe |
| Wzorcowy zakres danych (`aed-standard/`) | Słownik 43 pól (XLSX), schemat Table Schema, szablon i przykład CSV, mapowania źródeł, walidator i testy, dokumentacja | Przyjęcie zakresu i zasad (dysponent jako odpowiedzialny, brak danych osobowych, licencja każdego źródła) |
| Uruchomienie portalu | Konfiguracja lokalnego uruchomienia, dane startowe z kontami, dokumentacja uruchomienia | Kod portalu dane.gov.pl to oficjalny kod jego autorów (GPLv3), nie wygenerowany przez AI; opis zmian lokalnych: [do uzupełnienia po scaleniu konfiguracji portalu] |
| Moduły AED (agregator, kreator, walidator, strona akcji, zgłoszenia, "Najbliższy AED") | W realizacji: kod backendu i frontendu, testy, dane demonstracyjne. [Do uzupełnienia po scaleniu modułów.] | Zakres funkcji i priorytety; akceptacja działania w demo [do uzupełnienia] |
| Nazwa, hasło, logo, księga znaku (`brand/`) | Kilka rund propozycji nazw i haseł oraz szkiców znaku; finalne pliki znaku i naklejki z kodem QR zapisane jako SVG; eksport do PNG, JPG i PDF w przeglądarce Google Chrome i w programie ImageMagick; księga znaku. Model: Claude Fable 5.2. Kontur Polski pochodzi z danych Natural Earth (domena publiczna), a krój Figtree jest na licencji SIL Open Font License 1.1 | Wybór nazwy "Mapa Serc"; własne sformułowanie hasła "Wszystkie AED pod ręką."; odrzucenie wcześniejszych propozycji i wybór wariantu znaku; akceptacja finalnych plików |
| Teksty zgłoszenia i prezentacja | Wersje robocze opisu, listy ograniczeń, konspektu i slajdów, tego oświadczenia | Redakcja i akceptacja treści; wygłoszenie prezentacji |
| Kontrola jakości | Testy automatyczne i przeglądy kodu oraz treści w osobnych sesjach AI; kontrola modułów AED w przeglądarce [do uzupełnienia po scaleniu modułów] | Przegląd końcowy materiałów przed wysłaniem [do wykonania] i odpowiedzialność za całość |

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
