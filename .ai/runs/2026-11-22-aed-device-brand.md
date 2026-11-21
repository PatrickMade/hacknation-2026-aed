# Identyfikacja Mapa Serc na stronie urządzenia AED
Issue: APP-58
Run: 920825b8-dd22-4407-8597-68bca30d34b7
Source doc: .ai/specs/2026-11-22-aed-device-brand.md
Route: agreed small change (juror feedback via the coordinator)

## Progress
1. [x] Pasek akcji, przyciski w zieleni akcji, blok QR w stylu naklejki.
2. [x] Przeglądarka: desktop, 360 px, axe 0 naruszeń.
3. [ ] Pełny gate, review, PR, merge (po PR L1 polish i L4 compliance).

## Evidence
- Assets: frontend/src/assets/aed/mapa-serc-logo-kolor.svg is byte-identical to brand/logo/mapa-serc-logo-kolor.svg (SHA-256 compared); name and slogan come from aed-campaign.brand.ts. The logo-with-slogan file was tried first and dropped: its slogan rendered at about 7 px at this width, so the slogan is real text (18 px) next to the mark.
- Browser (Chrome, isolated stack, /pl/aed/<demo id>?zglos=1 with the QR card expanded): band shows logo (alt "Mapa Serc"), slogan, "Ten AED jest na Mapie Serc." and a link to /pl/aed; buttons use #087F45; QR card follows brand/naklejka-qr (green frame, logo, scan line, green footer with ID and dysponent).
- axe-core 4.10.2 on `main` (tags wcag2a/2aa/21a/21aa/22aa): 0 violations at 360x800 and at 1200 px. On the whole document axe also reports `aria-progressbar-name` (ng-progress, also on /pl/dataset) and `aria-allowed-attr` (#dropdownMenuLink in the portal header): both in the unchanged global shell, out of scope.
- 360 px: scrollWidth 360, no element overflows, all buttons >= 44 px.
- Full gate: source verifier, compose config, 62 Django tests OK, copy check, client config: all exit 0. Diff limited to the device page component and one copied SVG.
