# Dopracowanie materiałów dla jury: README, wynik seeda, kreator
Issue: APP-56

## Problem i obecny stan
Przegląd `main` dla jury wskazał cztery braki:
1. Wstęp README mówi, że funkcje AED są „rozwijane osobno”, choć `main` zawiera kreator i walidator, raport zbiorczy z OSM, zgłoszenia z kodem QR, stronę akcji `/pl/aed` i `brand/`. Akapit o użyciu AI pomija stronę akcji i znak. Brak krótkiej ścieżki demo.
2. API przechowuje odpowiedzi tabel zasobów (`ResourceTableView`, `@documented_cache(timeout=900)`, Redis, klucze `falcon-cache`) przez 15 minut. Odpowiedź zapisana przed zakończeniem indeksowania może przez ten czas pokazywać na `/pl/aed` 0 luk. Nie jest to opisane.
3. Pierwszy `seed_jury` na pustej bazie drukuje ślady `Organization.DoesNotExist`. Przyczyna: portal loguje każdy sygnał modelu na poziomie DEBUG z `exc_info=1` (`mcod/core/db/models.py`), a `get_or_create` tworzy instytucję wewnątrz obsługiwanego wyjątku `DoesNotExist`.
4. Krok 1 kreatora: axe-core (`target-size`) zgłasza 3 linki szablonu o wysokości 17 px, poniżej 24 px (WCAG 2.2 AA 2.5.8).

## Zmiana
1. Nowy wstęp i lista funkcji README zgodne z `main`, bezosobowo; sekcja „Demo w 10 minut”; pełny akapit o użyciu AI z odwołaniem do `submission/oswiadczenie-ai.md`.
2. Sekcja „Cache API po `aed_refresh`”: czekanie na opróżnienie kolejek Celery (`rabbitmqctl list_queues`) albo usunięcie kluczy `falcon-cache` z Redis.
3. `seed_jury` podnosi na czas swojego działania poziom loggera `signals` do INFO i przywraca go po zakończeniu. Sygnały nadal działają; zapis i wynik seeda bez zmian.
4. Linki szablonu w kroku 1 dostają klasę `aed-links` z minimalną wysokością 24 px (tylko szablony `backend/mcod/aed_wizard`).

## Kryteria akceptacji i weryfikacja
1. README: brak „rozwijane osobno”; lista funkcji obejmuje kreator, walidator, raport z OSM, zgłoszenia z QR, `/pl/aed` i `brand/`; akapit AI wymienia stronę akcji i znak; jest ścieżka demo. Przegląd treści.
2. Polecenia z sekcji cache wykonane na lokalnym stacku: klucz `falcon-cache/1.4/resources/<id>/data...` ma TTL 900, polecenie czyszczenia go usuwa, `list_queues` pokazuje kolejki.
3. Test `test_fresh_seed_prints_no_signal_tracebacks`: RED przed zmianą (18 rekordów z wyjątkiem), GREEN po niej; poziom loggera przywrócony; pozostałe testy seeda przechodzą. Pierwszy seed na tymczasowej pustej bazie wypisuje tylko wynik.
4. axe `target-size` na kroku 1 kreatora (konto edytora Krosna): 3 naruszenia przed zmianą, 0 po niej.
5. Pełna bramka `validation.commands`, niezależny review, merge przez `merge_gate.py`.

## Poza zakresem
Teksty w `submission/` (osobny lane; `ograniczenia.md`, `opis-projektu.md` i `akceptacja.md` 2.3 wspominają naruszenie z punktu 4), nowe funkcje, wygląd portalu poza kreatorem AED, ostrzeżenie upstream `UserWarning` rejestru serializerów przy każdej komendzie `manage.py`.
