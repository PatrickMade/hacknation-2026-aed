# Mapa Serc - mały symbol, numer 112 na naklejce i pola na adres

Issue: APP-66
Source doc: .ai/specs/2026-11-22-mapa-serc-small-symbol-112-url-slots.md
Route: agreed delivery (small change)
Evidence: zakres wynika z trzeciego przeglądu zgłoszenia w roli jury (ocena
identyfikacji); koordynator projektu przekazał go jako uzgodnioną zmianę.

## Problem

1. Symbol to kontur Polski z wyciętym sercem AED. Kontur ma 145 punktów, więc
   w 16 px zlewa się w plamę, a serce z błyskawicą przestaje być czytelne.
   Księga znaku nie ma wersji przygotowanej dla małych rozmiarów.
2. Naklejka z kodem QR nie mówi, co zrobić w nagłym przypadku, i nie ma
   adresu, który można wpisać, gdy kodu nie da się zeskanować.
3. Wzór plakatu dla dysponentów pokazuje przycisk "Udostępnij swoje AED",
   który w druku nie działa, i nie ma widocznego adresu strony.

## Outcome

- Symbol ma wersję małą dla wysokości 16-32 px: prostszy kontur, większe serce
  z błyskawicą. Księga znaku podaje próg, przy którym zmienia się wersję.
  Znak podstawowy, znak z hasłem i dotychczasowy symbol zostają bez zmian.
- Naklejka ma wiersz "W nagłym zatrzymaniu krążenia dzwoń 112" i pole na
  krótki adres karty urządzenia. W jej rogu jest znak z małym symbolem.
- Plakat ma pod przyciskiem widoczne pole na adres strony.
- Koncepcja w księdze mówi wprost, że serce z błyskawicą celowo nawiązuje do
  znaku AED zalecanego przez ILCOR.

## Scope

- `brand/logo/mapa-serc-symbol-maly-*` i `brand/logo/mapa-serc-logo-maly-*`:
  nowe pliki (wersje `kolor`, `mono`, `negatyw`; formaty SVG, PDF, PNG, JPG).
- `brand/naklejka-qr/`: nowy układ naklejki (SVG, PDF, PNG).
- `brand/plakat/`: pole na adres i nowa naklejka na wzorze (SVG, PDF, PNG).
- `brand/ksiega-znaku-mapa-serc.pdf`: wersja 1.2 - koncepcja, strona o polu
  ochronnym i wielkości (próg i wersja mała), strony naklejki, plakatu i plików.
- `brand/README.md`: te same zasady i lista plików.

Non-goals: zmiana rysunku znaku podstawowego, znaku z hasłem i pełnego
symbolu; nowe kolory i hasła; zmiany w portalu (`frontend/`, `backend/`),
prezentacji i tekstach zgłoszenia.

## Acceptance

1. Dotychczasowe pliki `brand/logo/mapa-serc-{logo,logo-haslo,symbol}-*`
   i `brand/tokens.css` są bez zmian (`git diff --stat origin/main` dla tych
   ścieżek jest puste).
2. W `brand/logo/` są pliki `symbol-maly` i `logo-maly` w trzech wersjach
   i czterech formatach; pliki SVG nie mają osadzonych bitmap, elementów
   tekstowych ani odwołań do krojów.
3. Mały symbol wyrenderowany w 16 px pokazuje serce i błyskawicę wyraźniej niż
   pełny symbol w tej samej wielkości (porównanie obrazów w powiększeniu).
4. Księga znaku (`pdftotext`) podaje próg 32 px i 10 mm, wersję 1.2 oraz
   zawiera słowo "ILCOR"; strona z wielkościami pokazuje obie wersje.
5. Naklejka zawiera wiersz "W nagłym zatrzymaniu krążenia dzwoń 112" i pole na
   krótki adres; kod QR na PNG nadal dekoduje się do adresu przykładowego.
6. Plakat ma pod przyciskiem pole na adres; strona PDF ma format A4.
7. Każda para kolorów użyta na naklejce i plakacie jest w tabeli kontrastów
   księgi; używane są tylko cztery kolory akcji.
8. `brand/README.md` wymienia nowe pliki, próg, wiersz 112 i oba pola na adres.
9. Nowe i zmienione pliki nie zawierają prywatnych danych: ścieżek lokalnych,
   nazw kont, adresów e-mail (tekst, `strings` na plikach binarnych, `pdfinfo`).

## Verification

- Polecenia z punktów 1, 2, 4, 5, 6 i 9 oraz przegląd każdej zmienionej strony
  księgi, naklejki, plakatu i małego symbolu w 16, 24 i 32 px.
- Strony księgi, których treść się nie zmienia, porównane piksel po pikselu
  z wersją z `origin/main`.
- Bramka repozytorium: polecenia z `validation.commands`
  w `.ai/agentic.config.json`. Test portalu w Dockerze wykonuje kontrola CI
  `validation gate`; lokalnie nie jest uruchamiany, bo projekt Compose ma
  stałą nazwę i użyłby stosu należącego do innego zadania.
- QA: zmiana obejmuje tylko dokumenty i zasoby, więc `skip-qa`.
- Ograniczenia dowodu: pliki powstają z lokalnego skryptu, który nie jest
  częścią repozytorium; kolory i czytelność w druku nie były sprawdzane.

## Progress

- [x] 1. Mały symbol i znak z małym symbolem w `brand/logo/`
- [x] 2. Naklejka: wiersz 112, pole na krótki adres, znak z małym symbolem
- [x] 3. Plakat: pole na adres strony
- [x] 4. Księga znaku 1.2 i `brand/README.md`
- [ ] 5. Bramka walidacji i PR
