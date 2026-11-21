# Mapa zasobu: import Leaflet jako ESM
Issue: APP-49
Source doc: .ai/specs/2026-11-21-portal-leaflet-esm.md
Route: agreed delivery
Evidence: koordynator wskazał plik, linię, komunikat błędu i oczekiwaną poprawkę (import ESM).

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] RED w przeglądarce: zakładka Mapa zasobu CSV z rolami label/b/l pokazuje błąd `Dynamic require of "leaflet" is not supported`, brak `app-map`.
2. [x] Import ESM, wpis w UPSTREAM.md i w liście modyfikacji weryfikatora źródeł; GREEN w przeglądarce.
3. [ ] Pełna bramka, PR, niezależny review i merge przez merge_gate.py.

## Evidence
- Lokalny zbiór testowy (tylko w bazie stacka aed-portal): Krosno, 3 wiersze CSV `nazwa;szerokosc;dlugosc`, role geo przypisane jak w widgecie panelu, rewalidacja SUCCESS, `has_map=True`.
- RED: brak `app-map` i kontenera Leaflet; błąd konsoli `Dynamic require of "leaflet" is not supported`.
- GREEN po przebudowie dev servera (bez błędów kompilacji): kontener Leaflet 1084x600, 18 kafelków, 3 znaczniki; mapa regionów `/pl/dataset?isMapOpen=true` 32 kafelki. Jedyne pozostałe błędy konsoli to udokumentowane 404 pustego CMS (`/cms/api/pages/`).
