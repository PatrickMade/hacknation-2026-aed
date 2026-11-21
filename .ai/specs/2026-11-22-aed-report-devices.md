# Rejestr urządzeń z raportu zbiorczego AED i formularz bez obowiązkowych danych osobowych
Issue: APP-60
Extends: .ai/specs/2026-11-21-aed-reports.md, .ai/specs/2026-11-21-aed-report-retention.md

## Problem
Runda 2 jury: strona urządzenia, kod QR i zgłoszenie działają tylko dla pięciu fikcyjnych urządzeń demo. Rekordy opublikowanego „Raportu zbiorczego AED” nie mają strony urządzenia. Koordynator zdecydował też, że formularz zgłoszenia nie może wymagać danych osobowych.

## Zakres
1. Komenda `load_aed_report_devices` czyta główny plik CSV opublikowanego zasobu raportu (`ext_ident` `aed-raport-csv`, zbiór „Raport zbiorczy AED”) i dla każdego wiersza aktualizuje lub tworzy `AedDevice` po `aed_id`. Instytucja odpowiedzialna wynika z pierwszego rozpoznanego źródła w `source_records`:
   - `dane:dataset:<id>` - instytucja zbioru portalu z `ext_ident` `aed-src-<id>` (zbiory źródłowe publikowane przez agregator dla instytucji `jury-<slug>`);
   - `dysponent:<slug>` - instytucja o tym slugu (pliki opublikowane kreatorem).
   Wiersze bez rozpoznanej instytucji są pomijane i liczone. Urządzenie przypisane już do innej instytucji nie jest przenoszone (pominięte i liczone). Ponowne uruchomienie aktualizuje dane na miejscu. Kod agregatora nie jest importowany; komenda korzysta z danych portalu i formatu standardu.
   - Uruchomienie w demo: po `aed_refresh` (README).
2. Pole „Imię lub podpis” jest opcjonalne (API i formularz). Kontakt pozostaje opcjonalny i wymaga wyraźnej zgody. Klauzula mówi, że podanie danych osobowych nie jest wymagane. E-mail do dysponenta pokazuje „nie podano” przy braku imienia.

## Poza zakresem
Punkty OSM (brak potwierdzonego dysponenta); usuwanie urządzeń, które wypadły z raportu; zmiany w kodzie agregatora.

## 📝 Delta
ADDED
- WHEN operator uruchamia `load_aed_report_devices` po `aed_refresh` THEN każdy wiersz raportu z rozpoznaną instytucją ma urządzenie, stronę `/pl/aed/<aed_id>`, kod QR i ścieżkę zgłoszenia do tej instytucji.
MODIFIED
- WHEN zgłoszenie nie zawiera imienia ani kontaktu THEN API przyjmuje je (201). Kontakt bez zgody nadal daje 400.

## Kryteria akceptacji i weryfikacja
1. Testy Django: mapowanie `dane:dataset` i `dysponent:` na instytucje, pominięcie wierszy bez instytucji, brak przeniesienia cudzego urządzenia, idempotencja; zgłoszenie bez imienia przyjęte; kontakt bez zgody odrzucony.
2. Na żywo (izolowany stack): `aed_refresh`, potem komenda; liczba urządzeń równa liczbie wierszy raportu z rozpoznaną instytucją; zgłoszenie dla rekordu raportu widoczne tylko w panelu jego instytucji.
3. Przeglądarka: strona urządzenia z raportu; formularz bez obowiązkowego imienia; axe 0 naruszeń w treści strony.
4. Pełny gate, niezależny review, merge przez merge_gate.py.
