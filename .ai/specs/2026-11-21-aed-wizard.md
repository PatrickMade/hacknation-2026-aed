# Kreator dysponenta AED i publiczny walidator pliku
Issue: APP-43

## Cel i obecny stan
Dysponent AED ma dane w różnych układach plików (CSV z separatorem `;`, XLSX, GeoJSON). W lokalnym portalu nie ma drogi, by zamienić taki plik na zasób zgodny z profilem `aed-standard/` (PL 1.0.0) i opublikować go w zbiorze swojej instytucji. Nie ma też publicznej kontroli pliku bez logowania.

## Zakres
Nowa aplikacja Django `backend/mcod/aed_wizard/` w komponencie admin (admin.mcod.local):

1. Kreator "Dodaj dane AED" w panelu dostawcy, dostępny dla zalogowanego personelu, który ma co najmniej jedną instytucję (pełnomocnik, edytor) oraz dla superużytkownika. Instytucję wybiera się wyłącznie spośród `user.organizations` (superużytkownik: wszystkie).
   - Krok 1: pobranie szablonu (`template.csv`, `field-dictionary.xlsx`, `example.csv` z `aed-standard/`), wgranie CSV/XLSX/GeoJSON albo podanie URL http(s) do pliku.
   - Krok 2: przypisanie kolumn źródła do pól standardu z automatyczną podpowiedzią (nazwa pola, polska etykieta schematu, typowe aliasy), wartości domyślne pól wymaganych, licencja (CC0 1.0 albo CC BY 4.0) i data danych.
   - Krok 3: raport. Błędy blokujące pochodzą wyłącznie z `aed-standard/validate.py` uruchomionego na wygenerowanym CSV (wiersz, pole, komunikat; m.in. punkt poza ramką Polski, powtórzony `aed_id`). Ostrzeżenia kreatora nie blokują: prawdopodobnie zamienione osie (punkt poza Polską, a po zamianie w Polsce), możliwe duplikaty (te same współrzędne albo nazwa z adresem), godziny spoza składni OSM przeniesione do `opening_hours_raw`, nadane identyfikatory `aed_id`. Opcja kreatora zamienia osie w oznaczonych wierszach.
   - Krok 4: publikacja zasobu CSV w zbiorze AED dysponenta. Zbiór tworzony przy pierwszej publikacji: tytuł "Defibrylatory AED - <instytucja>", kategoria Zdrowie (HEAL), słowa kluczowe `AED`, `defibrylator`, `zgodny ze standardem AED`, częstotliwość aktualizacji, licencja. Zasób: status opublikowany, `data_date`, opis zaczynający się od "Zgodny ze standardem AED (profil PL 1.0.0)". Rekord `AedPublication` zapisuje znak zgodności (instytucja, zbiór, zasób, liczba rekordów, wersja profilu, autor, czas).
2. Publiczna strona "Sprawdź swój plik" (`/aed/sprawdz-plik/`, bez logowania): wgranie CSV/XLSX/GeoJSON, raport tym samym walidatorem. CSV jest sprawdzany bajt w bajt; XLSX i GeoJSON są zamieniane na CSV tylko przez kolumny o nazwach pól standardu (GeoJSON Point daje `latitude`/`longitude`). Nic nie jest zapisywane: plik tymczasowy jest usuwany po walidacji, bez cache i bez modelu.

## Ustalenia
- Logika walidacji pochodzi z `aed-standard/validate.py` i `schema.json`, ładowanych z katalogu `AED_STANDARD_DIR` (Compose montuje `./aed-standard` tylko do odczytu). Kreator nie kopiuje reguł; jego ostrzeżenia są dodatkową diagnostyką.
- Kształt zasobu dla agregatora L4 (umowa przez standard, nie przez wspólny kod): opublikowany zasób CSV UTF-8, CRLF, nagłówek będący podzbiorem pól profilu w kolejności `schema.json`, przechodzący `validate.py`, w zbiorze instytucji-dysponenta oznaczonym słowem kluczowym `AED`. `source_records[].source_id` = `dysponent:<slug instytucji>`.
- `aed_id`: wartość UUID ze źródła zostaje; w przeciwnym razie UUID5 z `dysponent:<slug>` i identyfikatora rekordu źródła (stały przy ponownym wgraniu tego samego źródła). Raport mówi, ile identyfikatorów nadano.
- Stan między krokami: token w sesji, tabela w cache portalu (redis) na 1 godzinę. Limit pliku 10 MB. URL: tylko http(s), adresy hosta rozwiązujące się do sieci prywatnych/pętli zwrotnej są odrzucane.
- Mapa podglądu (role `l`/`b`/`label`) zależy od asynchronicznego przetworzenia pliku przez portal i pozostaje do ustawienia w zakładce map; to ograniczenie wersji 1.

## Kryteria akceptacji i weryfikacja
1. Mapowanie: plik w układzie miejskim (`;`, polskie nagłówki, przecinek dziesiętny) daje CSV, które przechodzi `validate.py` - test Django `mcod.aed_wizard.tests`.
2. Walidacja: zamienione osie i punkt poza Polską dają błąd walidatora oraz ostrzeżenie o osiach; zamiana osi usuwa błąd; duplikaty i godziny spoza OSM dają ostrzeżenia - testy.
3. Publikacja: konto pełnomocnika publikuje plik; powstaje zbiór instytucji z kategorią HEAL, tagiem AED, licencją i zasób z plikiem CSV, `data_date` i znakiem zgodności; druga publikacja używa tego samego zbioru; obca instytucja jest odrzucona - test Django z klientem.
4. Publiczny walidator: anonimowy POST zwraca raport, nie tworzy obiektów w bazie i nie zostawia pliku - test.
5. End to end lokalnie: konto pełnomocnika przechodzi kreator w przeglądarce; zasób jest widoczny w API `/1.4`; agregator L4 odczytuje zasób, gdy jego PR jest dostępny (inaczej raportowane jako niezweryfikowane).
6. Pełny gate `validation.commands`, niezależny review i merge przez merge gate.

## Ryzyka i granice
Ostrzeżenie o duplikatach jest heurystyką; wspólny adres nie dowodzi tego samego urządzenia. Walidator nie sprawdza pełnej gramatyki `opening_hours`. Pobieranie URL jest prostą kontrolą dla lokalnego demo, nie pełną ochroną SSRF.

## Poza zakresem
Agregacja i deduplikacja między źródłami (L4), zgłoszenia (L7), strona akcji (L6), zmiany walidatora `aed-standard/`, frontend Angular, wygląd portalu poza nowymi stronami AED.

## Plan wdrożenia
1. Spec i plan.
2. Moduł: odczyt plików, mapowanie, walidacja przez `aed-standard`, diagnostyka; testy RED/GREEN.
3. Widoki kreatora, publikacja, publiczny walidator, menu, URL, Compose; testy.
4. Weryfikacja w przeglądarce, pełny gate, PR, niezależny review, merge.
