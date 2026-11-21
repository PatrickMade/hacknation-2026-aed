# Identyfikacja Mapa Serc na stronie urządzenia AED z kodu QR
Issue: APP-58
Extends: .ai/specs/2026-11-21-aed-reports.md

## Problem
Juror zauważył, że strona urządzenia `/pl/aed/<aed_id>`, którą otwiera kod QR z naklejki, nie pokazuje identyfikacji akcji „Mapa Serc”, choć naklejka ją ma.

## Zakres
- Pasek akcji na górze treści strony urządzenia (w każdym stanie strony): gotowy znak `brand/logo/mapa-serc-logo-kolor.svg` (alt: nazwa), hasło „Wszystkie AED pod ręką.” jako tekst obok znaku (w pliku ze znakiem i hasłem hasło miało ok. 7 px przy tej szerokości i było nieczytelne), zdanie „Ten AED jest na Mapie Serc.” i link „Czym jest akcja Mapa Serc?” do strony akcji `/pl/aed`.
- Przyciski tej strony w zieleni akcji (`brand/tokens.css`: #087F45, przy fokusie/najechaniu #0B2E20, biały tekst 5.1:1 i 14.7:1). Style są ograniczone do komponentu strony urządzenia.
- Blok kodu QR w stylu `brand/naklejka-qr`: zielona ramka z zaokrągleniem, znak `mapa-serc-logo-kolor.svg`, kod QR, „Ten AED jest na Mapie Serc”, „Zeskanuj: sprawdź dane albo zgłoś usterkę”, zielona stopka z identyfikatorem AED i dysponentem.
- Znaki to gotowe pliki skopiowane bajt w bajt do `frontend/src/assets/aed/` (jak symbol na stronie akcji); nazwa i hasło pochodzą z `aed-campaign.brand.ts`. Księga znaku zabrania składania znaku z liter i zmiany kolorów.

## Poza zakresem
Nagłówek portalu, nawigacja, układ i inne strony; nowe materiały marki.

## Kryteria akceptacji i weryfikacja
1. Przeglądarka: pasek akcji, link do `/pl/aed` i blok naklejki widoczne na `/pl/aed/<aed_id>`; inne strony bez zmian (diff dotyczy tylko komponentu strony urządzenia i skopiowanego pliku SVG).
2. axe-core: 0 naruszeń w treści strony urządzenia przy zamkniętym i otwartym formularzu; przycisk „Zgłoś problem” nie ma `aria-controls` wskazującego niewyrenderowany formularz. Dwa elementy globalnej powłoki portalu (ng-progress, menu w nagłówku) są ograniczeniem upstream.
3. 360 px: brak przewijania w poziomie; przyciski min. 44 px.
4. Pliki SVG identyczne z `brand/logo` (porównanie sum SHA-256).
5. Pełny gate, niezależny review, merge przez merge_gate.py.
