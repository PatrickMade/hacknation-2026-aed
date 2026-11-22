# Grupa radio i zawijanie nazwy pliku
Issue: APP-69
Run: 21dfc010-fd84-490a-a57c-0880a642301d
Source doc: .ai/specs/2026-11-22-aed-radio-group.md
Route: agreed small change (final integration QA via the coordinator)

## Progress
1. [x] name="type" dla radio; overflow-wrap w walidatorze.
2. [x] Klawiatura i axe (desktop, 360 px); walidator 360 px; gate.
3. [ ] PR, review, merge do 07:30 UTC.

## Evidence
- RED (from the final integration QA on main 9f4f505): radios without a shared name were separate tab stops and arrows did not move within the group; the validator heading clipped a long filename at 360 px.
- Radio group (Chrome, isolated stack, /pl/aed/<demo id>?zglos=1), real key presses from the form heading: desktop 1200 px - Tab lands on `type-closed`, next Tab on `description` (one tab stop for the group), Shift+Tab then ArrowDown twice checks `type-damaged`; 360x800 - Tab `type-closed`, Tab `description`, Shift+Tab + ArrowDown checks `type-missing`. All 4 radios have name="type" inside the fieldset with its legend. axe-core 4.10.2 on `main` at 360 px: 0 violations; scrollWidth 360. Submitting after the arrow choice: "Zgłoszenie nr 6 zostało przyjęte"; stored type `missing` (behaviour unchanged).
- Validator (/aed/sprawdz-plik/, 96-character filename, rendered page opened at 360x800): with the rule h2 scrollWidth 294 = clientWidth 294, page scrollWidth 360; with the rule disabled in the page h2 scrollWidth 1034, page 1067.
- Full gate: source verifier, compose config, 93 Django tests OK, copy check, client config: all exit 0. Prettier (repo config) clean.
