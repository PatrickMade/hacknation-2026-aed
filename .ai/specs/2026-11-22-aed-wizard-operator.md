# Dysponent w kreatorze AED: z pliku albo wpisany, nigdy instytucja wgrywająca
Issue: APP-63
Covers part of: .ai/specs/2026-11-21-aed-wizard.md (krok 2 kreatora, pole `operator_name`)

## Problem
Kreator wypełnia pole „Dysponent (operator_name), gdy brak kolumny” nazwą instytucji wgrywającej plik (`backend/mcod/aed_wizard/forms.py`, `initial=organization.title`), a `mapping.convert` wpisuje tę wartość do każdego rekordu bez dysponenta. Urząd miasta, który publikuje listę AED w szkołach i przychodniach, zostaje wtedy potwierdzonym dysponentem urządzeń, których nie ma. Standard AED (`aed-standard/README.md`, pkt 3; opis pola w `schema.json`) wymaga potwierdzonego dysponenta i zakazuje kopiowania wydawcy zbioru lub właściciela budynku. Alias kolumny `wlasciciel` (właściciel) też kieruje do `operator_name`.

## Rezultat
- Kreator nie wpisuje dysponenta sam. Pole zastępcze jest puste, bez wartości początkowej.
- Gdy plik ma kolumnę dysponenta (przypisaną do `operator_name`), wartość pochodzi z pliku. Wpisana wartość uzupełnia tylko rekordy, w których kolumna jest pusta.
- Bez przypisanej kolumny wpisanie dysponenta jest wymagane. Podpowiedź wyjaśnia, że to potwierdzona instytucja odpowiedzialna za urządzenia i odbiór zgłoszeń, niekoniecznie instytucja wgrywająca, że nazwa obiektu ani właściciel budynku nie są potwierdzeniem i że publikacja dysponenta nie może użyć wartości „nieustalony”.
- Krok 1 nazywa instytucję wgrywającą „Instytucja publikująca dane”, a nie „dysponent AED”.
- Alias `wlasciciel` nie przypisuje już kolumny do `operator_name`.
- Raport walidacji pokazuje pochodzenie dysponenta: liczbę rekordów z kolumny pliku (z nazwą kolumny) i liczbę rekordów z wartością wpisaną.
- Reguła standardu zostaje bez zmian: `validate.py` odrzuca w publikacji dysponenta (`source_id` = `dysponent:...`) wartość `nieustalony` i flagę `operator_unconfirmed`.

## Zakres
`backend/mcod/aed_wizard/`: `mapping.py` (brak domyślnej wartości, liczniki pochodzenia, alias), `forms.py` (pole i walidacja), `views.py` (stan raportu), szablony kroku 2 i raportu, testy. Bez zmian w `aed-standard/`, agregatorze, modelach i opublikowanych zasobach.

## Kryteria akceptacji
1. Plik bez kolumny dysponenta (układ Krosna): pole puste; wysłanie bez wpisu daje błąd pola i nie przechodzi do raportu - test widoku.
2. Plik z kolumną `Dysponent`: przejście bez wpisu; rekordy mają wartości z pliku; raport pokazuje „z pliku (kolumna Dysponent)” - test widoku.
3. Wartość wpisana: raport pokazuje „wpisany: …” z liczbą rekordów; opublikowany plik ma tę wartość - test widoku.
4. `mapping.convert` bez kolumny i bez wpisu nie wstawia żadnej wartości (walidator zgłasza `operator_name: wartość wymagana`) - test mapowania.
5. Wpis „nieustalony” jest odrzucany przez walidator w raporcie - test widoku.
6. Pełna bramka `validation.commands`, niezależny review, merge przez merge gate.

## Weryfikacja
Testy RED przed zmianą, potem GREEN; pełna bramka.

## Progress
1. [x] Task record.
2. [x] Testy RED, implementacja, GREEN.
3. [ ] Pełna bramka, PR, niezależny review, merge.

## Evidence
- RED (unfixed code), 4 of the 6 new tests: `'Krosno' not found in (None, '')` (field pre-filled with the uploading institution); report without "Dysponent: z pliku (kolumna Dysponent) w 2 rekordach" and without "Dysponent: wpisany …"; `'operator_name' unexpectedly found in {... 'operator_name': 'właściciel'}`. The other 2 already passed on unfixed code and stay as guards: the placeholder refusal (existing `validate.py` rule) and `convert` with an empty entry.
- GREEN: `mcod.aed_wizard` 33 tests OK.
- Browser (isolated stack, krosno.agent, real Krosno file): empty dysponent field with help text linked by `aria-describedby`; submit without it shows "Podaj dysponenta urządzeń albo przypisz kolumnę dysponenta z pliku." and stays on step 2; with an entry the report shows "Dysponent: wpisany „Miejski Ośrodek Sportu w Krośnie” w 21 rekordach."
- Review of 1a0cfd88 (APPROVE, record https://github.com/PatrickMade/hacknation-2026-aed/pull/26#pullrequestreview-6009787736): minors 1-2 applied (hint says "Potwierdzona instytucja" and warns against facility name/building owner; step-1 label "Instytucja publikująca dane"). Nit 3 (field error not linked to the input) unchanged, same pattern as before.
