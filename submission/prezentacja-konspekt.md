# Konspekt prezentacji

Format końcowy: PDF, najwyżej 10 MB, co najmniej 5 slajdów. Prezentacja
na żywo w finale: do 5 minut. Każdy slajd z dowodem ma wskazany zrzut
ekranu do wykonania (oznaczenie **Zrzut**). Zrzuty powstaną z lokalnego
portalu po scaleniu modułów AED.

## Slajd 1. Tytuł

- Nazwa i hasło akcji, znak. [Do uzupełnienia po wyborze marki.]
- Podtytuł: jeden standard danych o defibrylatorach w dane.gov.pl.
- Zadanie: "Misja AED - Dane na ratunek", Ministerstwo Cyfryzacji.

## Slajd 2. Problem

- 5 zbiorów AED w dane.gov.pl, każdy w innym układzie; w Markach rekord
  zakodowany w jednej kolumnie i zamienione współrzędne.
- 739 wpisów o AED na 20 stronach urzędów, tylko 137 ze współrzędnymi.
- Ponad 18 tysięcy punktów w OSM, bez wskazania odpowiedzialnego dysponenta.
- Wniosek: brak jednego, aktualnego, maszynowo czytelnego źródła.
- **Zrzut:** fragmenty dwóch istniejących zbiorów w różnych układach.

## Slajd 3. Rozwiązanie: mechanizm w portalu

- Schemat przepływu: dysponent, kreator, walidacja, zasób dysponenta,
  raport zbiorczy AED, mapa i API, służby i aplikacje.
- Dysponent odpowiada za swoje dane; raport zbiorczy publikuje operator
  portalu na wzór zbioru 4354 (raport zbiorczy DGA).
- Oficjalny kod portalu, wygląd portalu bez zmian.

## Slajd 4. Wzorcowy zakres danych AED

- 43 pola: 15 wymaganych, 3 warunkowe, 25 opcjonalnych.
- Pliki: słownik XLSX, szablon CSV, Table Schema, walidator z testami,
  mapowania 5 zbiorów i OSM.
- Kluczowe pola: lokalizacja WGS84, TERYT, dostępność i `opening_hours`,
  dysponent, stan, przegląd, pochodzenie i licencja rekordu.
- Bez danych osobowych.
- **Zrzut:** słownik pól w XLSX.

## Slajd 5. Kroki użytkownika: dysponent

1. Panel dostawcy, "Dodaj dane AED".
2. Wgranie pliku lub URL.
3. Dopasowanie kolumn.
4. Raport walidacji z błędami do wiersza i pola.
5. Publikacja z metadanymi i znakiem zgodności.

- **Zrzuty:** kreator (krok mapowania), raport walidacji, opublikowany
  zasób w zbiorze dysponenta.

## Slajd 6. Kroki użytkownika: odbiorca danych

1. Zbiór "Raport zbiorczy AED" w portalu.
2. Mapa z punktami AED i filtrem odległości ("Najbliższy AED").
3. Pobranie CSV lub GeoJSON i odczyt przez API `/1.4`.
4. Kod QR przy urządzeniu, zgłoszenie problemu do dysponenta.

- **Zrzuty:** raport zbiorczy z zasobami, mapa, odpowiedź API, formularz
  zgłoszenia, zgłoszenie w panelu dysponenta.

## Slajd 7. Dowody wymagań technicznych

| Wymaganie | Dowód |
|---|---|
| Zgodność z zasadami dane.gov.pl | Instytucja, zbiór, zasób i metadane w panelu portalu |
| Formaty maszynowo czytelne | CSV, GeoJSON, JSON z API, słownik XLSX |
| Dane z wielu źródeł w jednym zbiorze | Raport zbiorczy z pochodzeniem każdego rekordu |
| Aktualność | Zadanie odświeżania i data danych w metadanych |
| WCAG 2.2 AA | Wynik kontroli dostępności nowych stron AED |
| Responsywność | Strona akcji i formularz na ekranie 360 px |

- **Zrzuty:** metadane zasobu, wynik kontroli dostępności, widok mobilny.

## Slajd 8. Akcja dla dysponentów

- Nazwa, hasło, logo, naklejka z kodem QR przy urządzeniu.
- Strona akcji w portalu: liczniki, mapa pokrycia gmin, przycisk do kreatora.
- **Zrzuty:** strona akcji, mapa pokrycia, naklejka.

## Slajd 9. Ograniczenia

- Lokalna instancja portalu, bez publikacji na produkcji.
- Dane demonstracyjne i brak fizycznej weryfikacji urządzeń.
- OSM na ODbL jako osobny zasób; publikacja ODbL wymaga uzgodnienia.
- Granice walidacji (TERYT, `opening_hours`, dane osobowe w tekście).
- Pełna lista: `submission/ograniczenia.md`.

## Slajd 10. Użycie AI i dalsze kroki

- Zakres użycia AI w skrócie, pełne oświadczenie: `submission/oswiadczenie-ai.md`.
- Wdrożenie: te same mechanizmy w produkcyjnym dane.gov.pl, zaproszenie
  pierwszych dysponentów, codzienny raport zbiorczy.
- Link do repozytorium.
