# Mapa Serc - znak akcji

Materiały graficzne akcji, która zachęca do udostępniania danych
o defibrylatorach AED w portalu dane.gov.pl.

- Nazwa akcji: **Mapa Serc**
- Hasło: **Wszystkie AED pod ręką.**
- Hasło dla dysponentów: **Lista AED w szufladzie nikogo nie uratuje.**
- Zasady użycia: [ksiega-znaku-mapa-serc.pdf](ksiega-znaku-mapa-serc.pdf)

## Pliki

| Ścieżka | Zawartość |
|---|---|
| `logo/mapa-serc-logo-*` | Znak podstawowy: symbol i nazwa w układzie poziomym |
| `logo/mapa-serc-logo-haslo-*` | Znak z hasłem |
| `logo/mapa-serc-symbol-*` | Sam symbol |
| `logo/mapa-serc-symbol-maly-*` | Symbol w wersji małej, gdy ma mniej niż 32 px wysokości |
| `logo/mapa-serc-logo-maly-*` | Znak podstawowy z małym symbolem |
| `naklejka-qr/` | Wzór naklejki z kodem QR do umieszczenia przy urządzeniu |
| `plakat/` | Wzór plakatu dla dysponentów (SVG, PDF w formacie A4, podgląd PNG) |
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
- Gdy symbol ma mniej niż 32 px wysokości na ekranie albo 10 mm w druku,
  używaj wersji małej (`symbol-maly`, `logo-maly`): ma prostszy kontur oraz
  większe serce i błyskawicę. Od tego progu w górę używaj wersji pełnej.
- Najmniejsza wysokość symbolu w wersji małej: 16 px na ekranie, 5 mm w druku.
- Serce z błyskawicą celowo nawiązuje do międzynarodowego znaku AED
  zalecanego przez ILCOR, bo ten motyw jest rozpoznawany na całym świecie.
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

Wzór w `naklejka-qr/` zawiera adresy przykładowe. Kod dla konkretnego
urządzenia powinien prowadzić do jego karty i do zgłoszenia usterki, które
trafia do dysponenta. Pod kodem jest pole na krótki adres karty, dla osób,
które nie mogą zeskanować kodu, a niżej miejsce na identyfikator urządzenia
i nazwę dysponenta. Na dolnym pasku jest wiersz "W nagłym zatrzymaniu
krążenia dzwoń 112"; nie usuwa się go ani nie zmienia. W rogu naklejki jest
znak z małym symbolem. Zalecany rozmiar: 70 x 93 mm.

## Hasła

Akcja ma dwa hasła o różnych rolach:

- **Wszystkie AED pod ręką.** - hasło główne, dla każdego odbiorcy. Jest
  częścią znaku z hasłem.
- **Lista AED w szufladzie nikogo nie uratuje.** - hasło dla dysponentów,
  czyli instytucji i firm, które mają AED. Używa się go w pismach, na
  plakatach i w prezentacjach dla dysponentów oraz w części strony akcji
  skierowanej do nich.

Hasła dla dysponentów nie dopisuje się do znaku, nie używa w materiałach dla
mieszkańców ani na naklejce przy urządzeniu. W materiale dla dysponentów jest
nagłówkiem, a hasło główne zostaje przy znaku. Oba hasła zapisuje się
w pełnym brzmieniu, z kropką na końcu.

## Plakat dla dysponentów

Wzór w `plakat/` jest przeznaczony do wywieszenia w urzędzie, szkole,
przychodni albo firmie. Ma format A4 i te same proporcje co A3. Pole
w prawym górnym rogu to miejsce na znak dysponenta. Pod przyciskiem jest
pole na adres strony, pod którym dysponent udostępnia dane: plakat jest
drukowany, więc adres musi być widoczny. Treść trzech kroków
można dopasować do własnej instrukcji; kolorów, kroju i brzmienia haseł
się nie zmienia.

## Źródła i licencje

- Krój pisma: Figtree, licencja SIL Open Font License 1.1.
- Kontur Polski: Natural Earth, granice państw w skali 1:10 000 000, domena
  publiczna; odwzorowanie PL-1992 (EPSG:2180). Uproszczenie konturu w wersji
  pełnej nie przekracza 3 km; wersja mała ma kontur uproszczony do 15 punktów.
- Nazwę, hasło i wariant znaku wybrał autor projektu. Rysunki, pliki i księgę
  znaku przygotowano z użyciem AI; zakres opisuje
  [oświadczenie o wykorzystaniu AI](../submission/oswiadczenie-ai.md).
