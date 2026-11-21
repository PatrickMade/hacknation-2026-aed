# Mapa Serc - logo, naklejka QR i księga znaku

Issue: APP-48
Source doc: .ai/specs/2026-11-21-mapa-serc-brand.md
Brief: .ai/specs/briefs/2026-11-21-kierunek-kampanii-aed.md
Route: agreed delivery (small change)
Evidence: nazwę "Mapa Serc" i hasło "Wszystkie AED pod ręką." wybrał właściciel
21 listopada 2026 r.; koordynator potwierdził zakres (logo, naklejka QR, księga
znaku, katalog `brand/`).

## Problem

Zadanie "Misja AED - Dane na ratunek" wymaga nazwy akcji, hasła, logotypu
w formatach .jpg, .png, .pdf i jednym formacie otwartym oraz księgi znaku
w PDF (kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia,
opis koncepcji w 3-5 zdaniach). Logotyp i hasło to 25% oceny. W repozytorium
są tylko szkice kierunków w `brand-directions/`, a strona akcji (APP-44)
czeka na znak i kolory.

## Outcome

Nowy katalog `brand/` z gotowym znakiem akcji "Mapa Serc", naklejką z kodem
QR do umieszczenia przy urządzeniu i księgą znaku. Znak jest prosty, czytelny
dla każdego odbiorcy i nie naśladuje oznakowania gov.pl ani dane.gov.pl.
Wariant znaku: serce z błyskawicą AED w kształcie znacznika mapy (wariant 1
ze szkiców), o ile właściciel nie wskaże innego do 18:30 UTC 21 listopada.

## Scope

- `brand/logo/` - znak w układzie poziomym, znak z hasłem i sam symbol;
  każdy w wersji kolorowej, jednobarwnej i negatywowej; formaty SVG, PNG,
  JPG i PDF.
- `brand/naklejka-qr/` - naklejka z kodem QR jako zastosowanie znaku
  (SVG, PNG, PDF). Kod QR zawiera adres przykładowy.
- `brand/ksiega-znaku-mapa-serc.pdf` - księga znaku: koncepcja (3-5 zdań),
  budowa i wersje znaku, kolory z kontrastem WCAG dla par kolorów, pole
  ochronne, minimalna wielkość, typografia, niedozwolone użycia, naklejka QR,
  znak obok miejsca na znak dane.gov.pl.
- `brand/tokens.css` - kolory jako zmienne CSS dla strony akcji.
- `brand/README.md` - spis plików, zasady użycia w skrócie, licencja kroju.
- `submission/oswiadczenie-ai.md` i `submission/lista-kontrolna.md` -
  aktualizacja o materiały marki.
- Usunięcie `brand-directions/` (szkice zastąpione przez `brand/`).

Non-goals: zmiany wyglądu portalu, rejestracja znaku towarowego lub domeny,
animacja, gadżety, zestaw do mediów społecznościowych, nowe propozycje nazwy
lub hasła, kod generujący kody QR dla urządzeń (APP-45).

## Acceptance

1. W `brand/logo/` są trzy układy (poziomy, z hasłem, symbol), każdy w trzech
   wersjach (kolor, mono, negatyw) i w czterech formatach (svg, png, jpg, pdf):
   36 plików (`ls brand/logo | wc -l`).
2. Pliki SVG nie zawierają osadzonych bitmap ani odwołań do krojów
   (`grep -L "<image\|font-family" brand/logo/*.svg` zwraca wszystkie).
3. Księga znaku jest plikiem PDF i zawiera sekcje: koncepcja, kolorystyka,
   pole ochronne, minimalna wielkość, niedozwolone użycia, naklejka QR
   (`pdftotext` i wyszukanie nagłówków).
4. Opis koncepcji ma od 3 do 5 zdań.
5. Dla każdej pary kolorów tekstu i tła użytej w księdze podany jest
   współczynnik kontrastu WCAG, zgodny z obliczeniem ze wzoru WCAG 2.x.
6. Kod QR na naklejce daje się odczytać i zawiera adres przykładowy
   (`zbarimg` na wyrenderowanym PNG).
7. Znak nie używa orła, biało-czerwonej belki ani granatu portalu; księga
   pokazuje go obok miejsca na znak dane.gov.pl.
8. Oświadczenie o użyciu AI obejmuje materiały marki.

## Verification

- Polecenia z punktów 1-3 i 6 oraz przegląd wyrenderowanych stron księgi
  znaku (każda strona obejrzana po wygenerowaniu).
- Bramka repozytorium: `fvm flutter analyze`, `fvm flutter test`,
  `python3 -B .ai/scripts/check_project_copy.py`,
  `python3 -B .ai/scripts/check_client_config.py`.
- QA: zmiana obejmuje tylko dokumenty i zasoby, więc `skip-qa`.
- Ograniczenia dowodu: kolizje nazwy sprawdzone tylko wyszukiwaniem w sieci
  (bez UPRP i EUIPO); wartości CMYK w księdze są orientacyjne, bez próby
  drukarskiej.

## Progress

- [ ] 1. Finalny znak w SVG (trzy układy, trzy wersje) i `brand/tokens.css`
- [ ] 2. Eksport znaku do PNG, JPG i PDF
- [ ] 3. Naklejka QR (SVG, PNG, PDF) z odczytem kodu
- [ ] 4. Księga znaku PDF
- [ ] 5. `brand/README.md`, oświadczenie AI, lista kontrolna, usunięcie `brand-directions/`
- [ ] 6. Bramka walidacji i PR
