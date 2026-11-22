# Dopracowanie materiałów dla jury
Issue: APP-56
Source doc: .ai/specs/2026-11-21-jury-polish.md
Route: agreed delivery
Evidence: koordynator określił cztery wyniki przeglądu `main` i oczekiwane zmiany.

Goal, scope, non-goals and risks: Source doc.

## Progress
1. [x] Seed: test RED (18 rekordów sygnałów z wyjątkiem), poprawka, GREEN (3 testy OK); pierwszy seed na tymczasowej pustej bazie wypisuje tylko wynik.
2. [x] Kreator: axe `target-size` przed zmianą 3 naruszenia (17 px), po zmianie 0 (20 przejść).
3. [x] Cache: klucz `falcon-cache` z TTL 900 potwierdzony, polecenie czyszczenia i `list_queues` wykonane.
4. [x] README: wstęp, funkcje, demo w 10 minut, cache, akapit AI.
5. [ ] Pełna bramka, PR, niezależny review, merge przez merge_gate.py po PR #14.
