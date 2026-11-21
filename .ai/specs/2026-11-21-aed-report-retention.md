# Klauzula RODO i 30-dniowa retencja danych zgłaszających AED
Issue: APP-51
Extends: .ai/specs/2026-11-21-aed-reports.md

## Cel
Decyzja właściciela projektu z 2026-11-21 (20:0x UTC) zamyka pytanie Q3 ze specyfikacji APP-45: treść klauzuli RODO i okres przechowywania danych zgłaszających.

## Zakres
1. Klauzula pod formularzem `/pl/aed/<aed_id>`: administratorem danych zgłaszającego (imię lub podpis, opcjonalny kontakt) jest dysponent urządzenia; operator portalu wyłącznie przekazuje zgłoszenie. Klauzula w UI i w README jest oznaczona jako wzór do weryfikacji prawnej.
2. Retencja: 30 dni po oznaczeniu zgłoszenia jako „rozwiązane” moduł usuwa `reporter_name` i `contact` (oraz zgodę na kontakt). Treść zgłoszenia (rodzaj, opis, status, notatka dysponenta, daty) zostaje.
   - `resolved_at` ustawia się przy zmianie statusu na „rozwiązane” i czyści przy powrocie do innego statusu (ponowne otwarcie zaczyna liczenie od nowa).
   - `personal_data_removed_at` zapisuje moment usunięcia; ponowne uruchomienie nie zmienia już wyczyszczonych zgłoszeń.
   - Usuwanie dotyczy danych w portalu; kopia w e-mailu wysłanym do dysponenta przy przyjęciu zgłoszenia podlega jego zasadom przechowywania (klauzula to mówi).
   - Uruchomienie: komenda `purge_aed_reporter_data [--days 30]` oraz zadanie Celery `mcod.aed_reports.tasks.purge_reporter_data_task` w harmonogramie dziennym (ten sam wzorzec co `aed_refresh`; lokalny Compose nie uruchamia celery beat, więc w demo uruchamia się komendę).
3. Panel pokazuje `resolved_at` i `personal_data_removed_at` tylko do odczytu.

## Poza zakresem
Ostateczne brzmienie prawne, usuwanie całych zgłoszeń, retencja innych danych portalu.

## 📝 Delta
MODIFIED
- WHEN zgłoszenie ma status „rozwiązane” od ponad 30 dni i uruchomi się komenda lub zadanie THEN imię/podpis i kontakt są puste, zgoda wyłączona, `personal_data_removed_at` ustawione, a opis i status bez zmian.
- WHEN zgłoszenie jest nowe, w trakcie albo rozwiązane krócej niż 30 dni THEN dane zostają.
- WHEN dysponent zmienia status z „rozwiązane” na inny THEN `resolved_at` jest czyszczone.
- WHEN ktoś otwiera formularz THEN klauzula wskazuje dysponenta jako administratora, operatora portalu jako przekazującego, 30-dniową retencję i dopisek o weryfikacji prawnej.

## Kryteria akceptacji i weryfikacja
1. Testy Django: usunięcie po 30 dniach, brak zmian dla nowszych/nierozwiązanych/już wyczyszczonych, ponowne otwarcie czyści `resolved_at`, komenda zwraca liczbę zmienionych zgłoszeń, formularz nadal wymaga imienia.
2. Migracja 0002: nowe pola i `reporter_name` z `blank=True` (pusty po usunięciu); `makemigrations --check` bez zmian.
3. Przeglądarka: nowa treść klauzuli na stronie urządzenia.
4. Pełny gate, niezależny review, merge przez merge_gate.py.

## Plan
1. Test RED retencji; pola, migracja, logika statusu, usuwanie, komenda, zadanie Celery (GREEN).
2. Klauzula w UI i README; weryfikacja w przeglądarce.
3. Pełny gate, review, PR, merge.

## Poprawka: kolejka zadania (APP-53)
Wpis harmonogramu `aed-reporter-data-retention` działa na kolejce `periodic` (`options.queue`), jak `aed-refresh-daily` po APP-52. Reguła upstream `backend/mcod/tests/test_celery.py` wymaga dla zadań celery beat kolejki innej niż `default`. Lokalny worker Compose działa bez `-Q` i konsumuje wszystkie kolejki z `CELERY_TASK_QUEUES`, więc zadanie wcześniej też się wykonywało; zmiana dotyczy zgodności z konwencją portalu. Weryfikacja: test Django sprawdzający nazwę zadania i kolejkę wpisu (RED bez opcji, GREEN z nią), pełny gate.
