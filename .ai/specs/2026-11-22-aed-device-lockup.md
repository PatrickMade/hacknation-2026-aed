# Lockup Mapa Serc z hasłem na stronie urządzenia AED
Issue: APP-64
Extends: .ai/specs/2026-11-22-aed-device-brand.md

## Problem
Runda 3 jury (marka): na stronie urządzenia z kodu QR nazwa ani hasło akcji nie mogą być złożone fontem portalu obok znaku; księga znaku wymaga gotowych plików z `brand/logo`. Na main 8dcdf64 pasek akcji pokazuje już oficjalny lockup `mapa-serc-logo-kolor.svg` (identyczny z `brand/logo`, napisy jako krzywe), ale hasło „Wszystkie AED pod ręką.” jest wpisane fontem portalu obok niego.

## Zmiana
- Pasek akcji używa lockupu z hasłem `brand/logo/mapa-serc-logo-haslo-kolor.svg` (skopiowanego bajt w bajt do `frontend/src/assets/aed/`, z wbudowanym polem ochronnym) zamiast wpisanego hasła. Alt: „Mapa Serc. Wszystkie AED pod ręką.”.
- Szerokość 300 px (max. 100% szerokości paska), aby hasło w znaku było czytelne; wcześniej przy 198 px miało ok. 7 px.
- Zdanie „Ten AED jest na Mapie Serc.” i link do strony akcji pozostają tekstem strony. Blok naklejki QR zostaje z lockupem bez hasła (jak naklejka).
- Strona akcji `/pl/aed` (L6) jest poza zakresem; wzorzec „symbol i wpisana nazwa” w jej nagłówku zgłoszono koordynatorowi.

## Kryteria akceptacji i weryfikacja
1. Plik lockupu identyczny z `brand/logo` (SHA-256); brak wpisanej nazwy i hasła obok znaku w pasku.
2. axe-core 0 naruszeń w treści strony przy zamkniętym i otwartym formularzu; 360 px bez przewijania w poziomie.
3. Pełny gate, niezależny review, merge przez merge_gate.py do 05:30 UTC.
