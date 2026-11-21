# Źródła prezentacji

| Ścieżka | Zawartość |
|---|---|
| `slajdy.html` | Treść slajdów, jeden `<section>` na slajd (1280 x 720 px) |
| `styl.css` | Układ i kolory akcji Mapa Serc (`brand/tokens.css`) |
| `img/zrzuty/` | Zrzuty ekranu z lokalnej instancji portalu (JPEG) |
| `img/brand/` | Znak, symbol i naklejka QR akcji, kopie plików z `brand/` |
| `fonts/` | Krój Figtree z licencją SIL Open Font License 1.1 (`OFL.txt`) |
| `build-pdf.py` | Budowa `../mapa-serc-prezentacja.pdf` |

## Budowa

```sh
python3 -B submission/prezentacja/build-pdf.py
```

Wymaga Pythona 3 oraz Chrome albo Chromium (ścieżkę można podać przez
`--chrome`). Skrypt drukuje `slajdy.html` w trybie bez interfejsu
i kończy się błędem, gdy PDF ma ponad 10 MB albo mniej niż 5 stron.
Każde uruchomienie nadpisuje `../mapa-serc-prezentacja.pdf` (nowa data
utworzenia w metadanych), więc po zmianie slajdów zatwierdź nowy PDF razem
ze źródłami.

## Zrzuty ekranu

Zrzuty pochodzą z lokalnej instancji portalu uruchomionej według
`README.md` w katalogu głównym, z kontami demonstracyjnymi i fikcyjnym
urządzeniem demo. Przeglądarka sterowana skryptem otwierała strony
w oknie 1440 x 900 px (telefon: 360 x 800 px). Pliki są przycięte
i zapisane jako JPEG. Nie zawierają haseł ani danych osobowych.

Kopie plików znaku w `img/brand/` pochodzą z katalogu `brand/` (księga
znaku Mapa Serc). Po zmianie znaku skopiuj je ponownie.
