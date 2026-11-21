# Zgłoszenie incydentu AED do dysponenta, kod QR i "Najbliższy AED"
Issue: APP-45

## 📝 TLDR
Osoba, która zastanie AED zamknięty, bez urządzenia, uszkodzony albo z błędnymi danymi, nie ma dziś w portalu drogi do odpowiedzialnego dysponenta. Zmiana doda publiczną stronę urządzenia (otwieraną kodem QR z naklejki) z formularzem "Zgłoś problem". Zgłoszenie trafi do panelu dostawcy tylko tej instytucji, która odpowiada za urządzenie, i wyśle e-mail (lokalnie MailHog). W Aplikacjach pojawi się wpis "Najbliższy AED" prowadzący do mapy raportu zbiorczego z istniejącym filtrem odległości.

## 📝 Problem Statement
Dane AED są odpowiedzialnością dysponentów (decyzja mentora, coordination.md 15:30). Bez kanału zgłoszeń błędy w danych i niedostępne urządzenia nie wracają do źródła. Wymóg demonstracji: zgłoszenie od końca do końca lokalnie, widoczne wyłącznie dla właściwego dysponenta.

## 📝 Proposed Solution
Nowa aplikacja Django `backend/mcod/aed_reports/` i jedna trasa frontendu `/pl/aed/<aed_id>`.

- **Rejestr urządzeń** `AedDevice`: podzbiór pól wzorcowego zakresu danych (`aed-standard/schema.json`): `aed_id` (UUID nadany przez dysponenta), `name`, `location_kind`, `latitude`, `longitude`, `locality`, `street_type`, `street`, `house_number`, `postcode`, `location_description`, `access`, `opening_hours`, `operational_status`, `operator_name`, oraz FK `organization` do instytucji portalu odpowiedzialnej za urządzenie. Ładowanie komendą `load_aed_devices --organization <slug> <plik.csv>` z CSV w układzie standardu (upsert po `aed_id`). Raport zbiorczy powstaje równolegle w L4; integracja = wywołanie tej komendy dla każdego dysponenta na pliku w układzie standardu. Kod L4 nie jest używany.
- **Zgłoszenie** `AedIncidentReport`: urządzenie, instytucja (kopiowana z urządzenia w chwili zgłoszenia), typ, opis, imię/nazwa zgłaszającego, opcjonalny kontakt, zgoda RODO, status, notatka dysponenta, daty.
- **API** (Falcon, zwykły JSON, bez JSON:API): odczyt urządzenia, utworzenie zgłoszenia, kod QR SVG.
- **Kod QR**: własny koder QR w module (tryb bajtowy, poziom korekcji M). Obrazy backendu i frontendu nie mają biblioteki QR; dodanie zależności wymagałoby przebudowy obrazów i zmiany zablokowanych plików upstream.
- **Panel dysponenta**: Django admin (admin.mcod.local), uprawnienia przez `django-rules` jak w innych modułach; queryset filtrowany po `request.user.organizations`; superadmin widzi wszystko. Bez dodawania zgłoszeń w panelu; dysponent zmienia status i notatkę.
- **E-mail**: po zapisie zgłoszenia `send_mail` do adresu instytucji i kont przypisanych do instytucji. Błąd SMTP nie cofa zgłoszenia; jest logowany.
- **"Najbliższy AED"**: komenda `seed_aed_showcase` tworzy/aktualizuje wpis `Showcase` (kategoria www) wskazujący mapę zasobu raportu zbiorczego `/pl/dataset/<id>/resource/<rid>/map`. Zasób szuka po tytule zbioru "Raport zbiorczy AED" albo przyjmuje `--url`.
- **Dane demonstracyjne**: fikcyjne urządzenia ("PRZYKŁAD FIKCYJNY") dla `jury-demo` i `jury-legionowo`, w pliku CSV w układzie standardu.

Odrzucone: odczyt urządzeń z indeksu Elasticsearch zasobu raportu zbiorczego (zależność od L4 i od struktury indeksu danych tabelarycznych); biblioteka QR w npm/Pipfile (przebudowa obrazów).

## 📝 Delta
ADDED
- WHEN ktoś otwiera `/pl/aed/<aed_id>` znanego urządzenia THEN widzi nazwę, adres, opis lokalizacji, dostęp, godziny, dysponenta i przycisk "Zgłoś problem".
- WHEN wysyła poprawny formularz THEN API zwraca 201 z numerem zgłoszenia, zgłoszenie ma status "nowe", a do skrzynki instytucji trafia e-mail.
- WHEN podaje kontakt bez zgody RODO THEN API zwraca 400 z błędem pola `consent`; nic nie jest zapisane.
- WHEN `aed_id` nie istnieje albo nie jest UUID THEN API zwraca 404, a strona pokazuje komunikat „Nie znaleziono urządzenia AED” (bez przekierowania na stronę 404 portalu).
- WHEN pełnomocnik lub edytor instytucji otwiera panel THEN widzi tylko zgłoszenia urządzeń swojej instytucji i może zmienić status (nowe, w trakcie, rozwiązane).
- WHEN ktoś pobiera `/aed/devices/<aed_id>/qr.svg` THEN dostaje SVG z kodem QR adresu strony urządzenia.
- WHEN operator uruchamia `seed_aed_showcase` THEN w Aplikacjach jest wpis "Najbliższy AED".

## 📝 API Contracts
- `GET /aed/devices/{aed_id}` → 200 `{"data": {aed_id, name, address, location_description, access, opening_hours, operational_status, operator_name, organization: {id, title}, latitude, longitude, report_url, qr_url, report_types: [{value, label}]}}`; 404 dla nieznanego.
- `POST /aed/devices/{aed_id}/reports` body `{"type", "description", "reporter_name", "contact"?, "consent"?}` → 201 `{"data": {"id", "status"}}`; 400 `{"errors": {pole: [komunikat]}}`.
  Walidacja: `type` z listy; `description` 1-2000 znaków; `reporter_name` 1-200; `contact` do 200 znaków; `consent` wymagane `true`, gdy `contact` niepusty.
- `GET /aed/devices/{aed_id}/qr.svg` → 200 `image/svg+xml`.

## 📝 Data Model
Nowe tabele `aed_reports_aeddevice` i `aed_reports_aedincidentreport` (jedna migracja początkowa). Dane osobowe: `reporter_name`, `contact` widoczne tylko w panelu właściwej instytucji i dla superadmina; nie trafiają do API publicznego ani do indeksu wyszukiwania. Okres przechowywania i automatyczne usuwanie są poza zakresem prototypu (ograniczenie do opisania).

## 📝 UI/UX
Strona w istniejącym układzie portalu (nagłówek i stopka bez zmian), komponenty i style portalu. Formularz: etykiety powiązane z polami, błędy przy polach i komunikat zbiorczy w `aria-live`, klauzula informacyjna RODO, przyciski min. 44 px, układ jednokolumnowy na 360 px. Tekst po polsku, bez "my".

## 📝 Edge Cases & Failure Scenarios
- Brak SMTP: zgłoszenie zapisane, błąd w logu, użytkownik dostaje sukces.
- Urządzenie bez współrzędnych: strona bez linku do mapy.
- Instytucja bez e-maila: e-mail tylko do kont instytucji; brak adresów → brak wysyłki, log.
- Spam: brak limitu zapytań w prototypie (ograniczenie).
- Treść POST powyżej 16 KB: 413 bez odczytu całości.
- Zawieszony SMTP: `EMAIL_TIMEOUT = 10` s; zgłoszenie jest już zapisane.
- Zgoda RODO: API przyjmuje wyłącznie JSON `true`.
- Strona korzysta z proxy `/api` serwera frontendu z Compose; budowa produkcyjna frontendu jest poza zakresem.

## 📝 Risks & Impact Review
Nowy publiczny endpoint zapisujący dane osobowe; ryzyko ograniczone do lokalnego demo. Wspólne pliki: jedna linia w `INSTALLED_APPS`, wpis w menu panelu, trasy w `mcod/routes.py` i w routingu frontendu (konflikty rozwiązuje późniejszy PR rebase'em). Zmiany w plikach upstream wymagają aktualizacji weryfikatora źródeł (`local/upstream-files.json`) zgodnie z AGENTS.md.

## Resolved assumptions (autonomous defaults)
- Q1 Źródło rejestru urządzeń przed L4: własny rejestr w module ładowany z CSV standardu - najmniejsza zależność od równoległej pracy; L4 może zasilać go tą samą komendą.
- Q2 Biblioteka QR: koder w module zamiast nowej zależności - brak przebudowy obrazów.
- Q3 Zgoda RODO wymagana tylko przy podanym kontakcie; imię/nazwa wymagane, z klauzulą informacyjną pod formularzem - zgodnie z briefem L7. ⚠ NEEDS HUMAN CONFIRMATION (treść klauzuli i okres przechowywania).

## 📋 Implementation Plan
Faza 1 - backend
1. Test RED: utworzenie zgłoszenia przez API, walidacja zgody, 404, zakres panelu, e-mail; potem modele, migracja, API, admin, reguły, e-mail (GREEN).
2. Koder QR z testem struktury i porównaniem z niezależnym koderem; endpoint SVG i podgląd QR w panelu urządzenia.
3. Komendy `load_aed_devices`, `seed_aed_showcase`, dane demonstracyjne; testy komend.

Faza 2 - frontend
4. Trasa `/pl/aed/:aedId`: strona urządzenia i formularz; weryfikacja w przeglądarce (desktop i 360 px, klawiatura).

Faza 3 - dostarczenie
5. Aktualizacja weryfikatora źródeł, README (sekcja AED) i oświadczenia o AI; pełny gate, niezależny review, PR do `main` po merge PR #3.
