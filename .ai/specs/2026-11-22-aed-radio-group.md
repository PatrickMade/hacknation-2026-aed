# Grupa radio w formularzu zgłoszenia AED i zawijanie nazwy pliku w walidatorze
Issue: APP-69
Extends: .ai/specs/2026-11-21-aed-reports.md

## Problem
Końcowa QA integracji (main 9f4f505), uwagi nieblokujące:
1. Radio „Rodzaj problemu” w formularzu zgłoszenia na stronie urządzenia nie mają wspólnego `name`, więc każde jest osobnym przystankiem Tab, a strzałki nie przesuwają wyboru w grupie.
2. Walidator `/aed/sprawdz-plik/` (moduł kreatora L5) przycina długą nazwę pliku w „Wynik dla pliku …” przy 360 px.

## Zmiana
1. `name="type"` na każdym radio w istniejącym `fieldset`/`legend` (zgodnie z `formControlName="type"`, czego wymaga Angular); walidacja i wysyłane wartości bez zmian.
2. `overflow-wrap: anywhere` dla nagłówków `h2` w szablonie walidatora (jedna reguła CSS).

## Kryteria akceptacji i weryfikacja
1. Klawiatura (desktop i 360 px): Tab trafia do grupy raz, strzałki zmieniają zaznaczone radio; axe 0 naruszeń w treści strony.
2. Walidator przy 360 px: nagłówek z długą nazwą pliku zawija się, bez przewijania w poziomie.
3. Gate, niezależny review, merge przez merge_gate.py do 07:30 UTC.
