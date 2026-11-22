# Lockup Mapa Serc z hasłem na stronie urządzenia AED
Issue: APP-64
Run: 69407c93-185c-4434-a69c-d155e6ce819a
Source doc: .ai/specs/2026-11-22-aed-device-lockup.md
Route: agreed small change (juror round 3 via the coordinator)

## Progress
1. [x] Lockup z hasłem zamiast wpisanego hasła; plik skopiowany bajt w bajt.
2. [x] Przeglądarka: 360 px i desktop, axe; pełny gate.
3. [ ] PR, review, merge do 05:30 UTC.

## Evidence
- Investigation (main 8dcdf64): the device page band already showed the official lockup `mapa-serc-logo-kolor.svg` (SHA-256 identical to brand/logo, no `<text>`), with the slogan typed in the portal font beside it; the campaign page `/pl/aed` (L6) hero shows the symbol with a typed `<h1>Mapa Serc</h1>` (reported to the coordinator, out of scope).
- Change: band uses `mapa-serc-logo-haslo-kolor.svg` (SHA-256 identical to brand/logo, no `<text>`, built-in clear space), alt "Mapa Serc. Wszystkie AED pod ręką.", 300 px wide (294 px rendered at 360 px); typed slogan removed.
- Browser (Chrome, isolated stack, report-backed device /pl/aed/cf598488-..., 360x800): lockup loads, band text is only "Ten AED jest na Mapie Serc. Czym jest akcja Mapa Serc?", no typed slogan; axe-core 4.10.2 on `main` 0 violations with the form closed and open; scrollWidth 360.
- Full gate on main 8dcdf64 + this change: source verifier, compose config, 87 Django tests OK, copy check, client config: all exit 0.
