# Dane demonstracyjne osobno i znak z hasłem na stronie Mapa Serc
Issue: APP-65
Rozszerza: `.ai/specs/2026-11-22-aed-campaign-publishers.md` (APP-59), `.ai/specs/2026-11-21-aed-campaign-page.md` (APP-44)

## Problem
Strona `/pl/aed` liczy 4 fikcyjnych dysponentów z `seed_aed_demo` jak dane oficjalne i potwierdzonych dysponentów: 12 z 86 rekordów, a 4 z 8 gmin (Gdańsk, Kraków, Poznań, Lublin) są na mapie zielone. Wszyscy trzej jurorzy w rundzie 3 obniżyli za to ocenę. Nagłówek strony wpisuje „Mapa Serc” czcionką portalu obok symbolu, czego księga znaku nie przewiduje.

## Rezultat
- Rekord demonstracyjny rozpoznaje znacznik, który `seed_aed_demo` zapisuje w źródle rekordu (`backend/mcod/aed_aggregate/demo.py`): wpis `source_records` z `source_id` zaczynającym się od `dysponent:` i `attribution` kończącym się na ` - dane demonstracyjne` (`DEMO_LABEL`). Agregator przenosi `source_records` bez zmian. Rekord jest demonstracyjny, gdy wszystkie jego źródła mają ten znacznik; rekord scalony ze źródłem oficjalnym liczy się jako oficjalny. Nazwa instytucji nie decyduje. Dane demonstracyjne zostają w raporcie.
- Liczniki: „Wydawcy danych o AED”, „Potwierdzeni dysponenci AED” i „Defibrylatory AED w raporcie zbiorczym” pokazują liczbę i „(w tym M demonstracyjnych)”, gdy M > 0 (odmiana: 1 demonstracyjny; dla rekordów 2-4 demonstracyjne). „Gminy z oficjalnymi danymi o AED” liczy tylko gminy z rekordami niedemonstracyjnymi i dopisuje „i N gmin tylko z danymi demonstracyjnymi”.
- Mapa: gmina, w której są tylko rekordy demonstracyjne, nie jest gminą z danymi oficjalnymi. Gdy OSM zna tam AED, zostaje luką (licznik, legenda i tabela luk, z dopiskiem „(tylko dane demonstracyjne)”); bez punktów OSM ma stan `demo` z wypełnieniem jak „brak danych”. Każda taka gmina ma fioletową przerywaną ramkę i pozycję legendy „Fioletowa ramka - tylko dane demonstracyjne (fikcyjne): N gmin”. Dymek podaje osobno AED w danych oficjalnych i demonstracyjnych. Tabela „Gminy z oficjalnymi danymi” obejmuje tylko gminy z danymi oficjalnymi i liczy tylko rekordy oficjalne. (Review 6009776306: wcześniejszy osobny kolor ukrywał 4 największe luki.)
- Krótka uwaga „Dane demonstracyjne”: fikcyjne instytucje oznaczone „dane demonstracyjne” pokazują, jak dysponent sam publikuje dane; nie opisują rzeczywistych urządzeń, dlatego liczniki podają je osobno, a gminy tylko z takimi danymi mają na mapie fioletową ramkę.
- Nagłówek: znak z hasłem `brand/logo/mapa-serc-logo-haslo-kolor.svg` (kopia bajt w bajt w `frontend/src/assets/aed/`) jako obraz w `h1` z tekstem alternatywnym „Mapa Serc. Wszystkie AED pod ręką.” zamiast symbolu, wpisanej nazwy i wpisanego hasła.

## Zakres
`frontend/src/app/pages/aed-campaign/` (obliczenia, odczyt raportu, komponent, testy), `frontend/src/assets/aed/mapa-serc-logo-haslo-kolor.svg` i ten spec. Bez zmian backendu i danych demonstracyjnych.

## Kryteria akceptacji i weryfikacja
1. Jest (RED, potem GREEN): rozpoznanie rekordu demonstracyjnego po znaczniku źródła (nie po nazwie: rekord z „(dane demonstracyjne)” w nazwie bez znacznika nie jest demonstracyjny); liczniki z częścią demonstracyjną; gmina tylko z danymi demonstracyjnymi nie jest liczona jako gmina z danymi oficjalnymi, a z punktami OSM zostaje luką; rekord scalony ze źródłem oficjalnym nie jest demonstracyjny; odmiana „demonstracyjny/-e/-ych”.
2. Plik znaku w `frontend/src/assets/aed/` jest identyczny z `brand/logo/mapa-serc-logo-haslo-kolor.svg` (`cmp`).
3. Przeglądarka na danych z `seed_aed_demo` i `aed_refresh`: liczniki z częścią demonstracyjną, 4 gminy z ramką demonstracyjną liczone jako luki, znak w nagłówku; axe 0 naruszeń w sekcji strony AED; 360 px bez przewijania w poziomie.
4. Pełna bramka `validation.commands`, niezależny review, wymagane CI, merge gate.

## Progress
1. [x] Issue APP-65, claim, spec.
2. [x] RED, potem GREEN: znacznik, liczniki, stan mapy (5 asercji RED); po review: luka przed stanem demonstracyjnym i rekord scalony (2 asercje RED), potem GREEN.
3. [x] Komponent, teksty, znak w nagłówku.
4. [ ] Przeglądarka, pełna bramka, PR, review, CI, merge gate.
