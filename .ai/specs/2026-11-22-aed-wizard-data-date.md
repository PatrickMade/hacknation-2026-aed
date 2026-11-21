# Data danych w kreatorze AED z danych, nie z dnia publikacji
Issue: APP-61
Covers part of: .ai/specs/2026-11-21-aed-wizard.md (krok 2 kreatora, metadane zasobu)

## Problem
Kreator „Dodaj dane AED” wypełnia pole „Data danych” (`data_date` zasobu) dzisiejszą datą (`backend/mcod/aed_wizard/forms.py`, `initial=timezone.localdate`). Plik Krosna z danymi z 2024-02-19 trafia do portalu jako dane z 2026-11-22. Data zasobu wprowadza w błąd odbiorców zbioru i jest też zapisywana jako `source_records[].source_data_date` rekordów.

## Rezultat
- Kreator odczytuje datę danych z pliku, gdy plik ją zawiera, w kolejności: najpóźniejsza `source_records[].source_data_date`, potem najpóźniejsza data z `updated_at`, potem z `retrieved_at` (kolumny standardu AED; wartości niepoprawne są pomijane).
- Wykryta data wypełnia pole i opis pola wskazuje jej źródło. Bez daty w pliku pole jest puste i wymagane, z komunikatem, że trzeba wpisać dzień, którego dotyczą dane. Kreator nie wpisuje dzisiejszej daty sam.
- Data z przyszłości jest odrzucana.
- Raport walidacji pokazuje datę danych i jej pochodzenie: „z pliku (pole …)”, „podana przez dysponenta” albo „podana przez dysponenta; w pliku …”, gdy dysponent zmienił wykrytą datę.

## Zakres
`backend/mcod/aed_wizard/`: wykrywanie daty (`mapping.py`), pole formularza (`forms.py`), stan i raport (`views.py`, `templates/aed_wizard/report.html`), testy. Bez zmian w `aed-standard/`, modelach, migracjach i już opublikowanych zasobach.

## Kryteria akceptacji
1. Wiersze standardu z `source_data_date`, z samym `updated_at` i bez dat dają odpowiednio tę datę, datę z `updated_at` i brak daty - test `mapping`.
2. Plik bez daty (układ Krosna): pole puste; wysłanie bez daty daje błąd pola i nie przechodzi do raportu - test widoku.
3. Plik z datą: pole wypełnione wykrytą datą; raport pokazuje datę i pochodzenie; opublikowany zasób ma tę `data_date` - test widoku.
4. Data z przyszłości daje błąd pola - test formularza.
5. Pełna bramka `validation.commands`, niezależny review, merge przez merge gate.

## Weryfikacja
Testy RED przed zmianą, potem GREEN; `docker compose run --rm manage python manage.py test mcod.aed_wizard`; pełna bramka.

## Progress
1. [x] Task record.
2. [x] Testy RED, implementacja, GREEN.
3. [ ] Pełna bramka, PR, niezależny review, merge.

## Evidence
- RED (unfixed code): `manage.py test` of the 6 new tests - `AttributeError: ... no attribute 'detect_data_date'` (3 mapping tests), `datetime.date(2026, 11, 22) not found in (None, '')`, `302 != 200` for a future date, `'2026-11-22' != '2024-02-19'` for the file date.
- GREEN: `mcod.aed_wizard` 27 tests OK.
- Browser (isolated stack, krosno.agent, real Krosno file): empty date field with help text linked by `aria-describedby`; submit without a date shows "Podaj datę danych..." and stays on step 2; with 2024-02-19 the report shows "Data danych: 2024-02-19 (podana przez dysponenta)".
