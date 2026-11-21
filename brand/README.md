# Mapa Serc - znak akcji

Materiały graficzne akcji, która zachęca do udostępniania danych
o defibrylatorach AED w portalu dane.gov.pl.

- Nazwa akcji: **Mapa Serc**
- Hasło: **Wszystkie AED pod ręką.**
- Zasady użycia: [ksiega-znaku-mapa-serc.pdf](ksiega-znaku-mapa-serc.pdf)

## Pliki

| Ścieżka | Zawartość |
|---|---|
| `logo/mapa-serc-logo-*` | Znak podstawowy: symbol i nazwa w układzie poziomym |
| `logo/mapa-serc-logo-haslo-*` | Znak z hasłem |
| `logo/mapa-serc-symbol-*` | Sam symbol |
| `naklejka-qr/` | Wzór naklejki z kodem QR do umieszczenia przy urządzeniu |
| `tokens.css` | Kolory akcji jako zmienne CSS |
| `ksiega-znaku-mapa-serc.pdf` | Księga znaku |

Każdy układ znaku ma trzy wersje: `kolor`, `mono` (jeden kolor) i `negatyw`
(na ciemne tło), a każda wersja cztery formaty:

- `svg` i `pdf` - wektorowe; tekst jest zamieniony na krzywe;
- `png` - przezroczyste tło;
- `jpg` - białe tło, a w wersji negatywowej ciemna zieleń.

Pliki mają wliczone pole ochronne, czyli wolny margines wokół znaku.

## Najważniejsze zasady

- Korzystaj z gotowych plików. Nie składaj znaku z liter, nie rozciągaj go,
  nie obracaj i nie zmieniaj kolorów.
- Na jasnym tle używaj wersji `kolor`, na ciemnym wersji `negatyw`.
- Najmniejsza wysokość symbolu: 16 px na ekranie, 5 mm w druku.
- Znak nie zastępuje znaku AED i nie oznacza miejsca, w którym jest urządzenie.
- Obok znaku dane.gov.pl znak akcji stoi jako równorzędny, w odstępie.
  Nie używa orła, biało-czerwonej belki ani barw portalu.

## Kolory

| Kolor | HEX | Zastosowanie |
|---|---|---|
| Zieleń | `#087F45` | Symbol, przyciski, akcenty |
| Ciemna zieleń | `#0B2E20` | Nazwa, hasło, tekst |
| Jasna zieleń | `#DDF3E6` | Tła sekcji |
| Biały | `#FFFFFF` | Tło podstawowe |

Kontrast par kolorów według WCAG jest podany w księdze znaku i w `tokens.css`.

## Naklejka z kodem QR

Wzór w `naklejka-qr/` zawiera adres przykładowy. Kod dla konkretnego
urządzenia powinien prowadzić do jego karty i do zgłoszenia usterki, które
trafia do dysponenta. Na dolnym pasku naklejki jest miejsce na identyfikator
urządzenia i nazwę dysponenta.

## Hasło pomocnicze

W materiałach kierowanych do dysponentów można użyć zdania:
"Lista AED w szufladzie nikogo nie uratuje."

## Źródła i licencje

- Krój pisma: Figtree, licencja SIL Open Font License 1.1.
- Kontur Polski: Natural Earth, granice państw w skali 1:10 000 000, domena
  publiczna; odwzorowanie PL-1992 (EPSG:2180). Uproszczenie konturu
  na potrzeby znaku nie przekracza 3 km.
- Nazwę, hasło i wariant znaku wybrał autor projektu. Rysunki, pliki i księgę
  znaku przygotowano z użyciem AI; zakres opisuje
  [oświadczenie o wykorzystaniu AI](../submission/oswiadczenie-ai.md).
