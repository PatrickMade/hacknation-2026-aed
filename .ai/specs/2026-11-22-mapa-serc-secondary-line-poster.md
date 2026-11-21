# Mapa Serc - hasło dla dysponentów i wzór plakatu w księdze znaku

Issue: APP-62
Source doc: .ai/specs/2026-11-22-mapa-serc-secondary-line-poster.md
Route: agreed delivery (small change)
Evidence: zdanie "Lista AED w szufladzie nikogo nie uratuje." autor projektu
zaakceptował 21 listopada 2026 r. jako dodatek do materiałów dla dysponentów;
zakres tej zmiany wynika z przeglądu zgłoszenia w roli jury.

## Problem

Zdanie "Lista AED w szufladzie nikogo nie uratuje." jest używane na stronie
akcji i w prezentacji, ale księga znaku (`brand/ksiega-znaku-mapa-serc.pdf`)
go nie definiuje. `brand/README.md` nazywa je tylko "hasłem pomocniczym", bez
zasad. Dysponent nie ma też gotowego wzoru plakatu. Logotyp i hasło to 25%
oceny, więc księga powinna opisywać wszystko, czym akcja się posługuje.

## Outcome

Księga znaku określa dwa hasła akcji i ich role: hasło główne "Wszystkie AED
pod ręką." dla każdego odbiorcy oraz hasło dla dysponentów "Lista AED
w szufladzie nikogo nie uratuje.", z zasadami użycia obu obok siebie. Księga
ma też stronę z wzorem plakatu dla dysponentów (A3/A4), który używa znaku,
obu haseł i naklejki z kodem QR. Wzór plakatu jest także plikiem w `brand/`.

## Scope

- `brand/ksiega-znaku-mapa-serc.pdf` - wersja 1.1: nowa strona "Hasła"
  (role i zasady użycia), nowa strona "Plakat dla dysponentów", zaktualizowana
  strona "Pliki". Pozostałe strony bez zmian treści poza numeracją.
- `brand/plakat/` - wzór plakatu dla dysponentów: SVG, PDF w formacie A4
  (te same proporcje co A3) i podgląd PNG.
- `brand/README.md` - hasło dla dysponentów jako oficjalne drugie hasło,
  zasady w skrócie, pliki plakatu.

Tekst plakatu (trzy kroki i wezwanie "Udostępnij swoje AED") pochodzi ze
szkicu ze slajdu 11 prezentacji (APP-55), żeby materiały mówiły to samo.

Non-goals: zmiany znaku, plików logo, naklejki i kolorów; nowe hasła; zmiany
prezentacji, strony akcji i tekstów zgłoszenia.

## Acceptance

1. Księga znaku ma strony "Hasła" i "Plakat dla dysponentów" (`pdftotext`
   i wyszukanie nagłówków) oraz zawiera oba hasła w pełnym brzmieniu.
2. Strona "Hasła" podaje rolę każdego hasła i zasady użycia obok siebie.
3. W `brand/plakat/` są pliki SVG, PDF i PNG wzoru plakatu; plakat zawiera
   znak, oba hasła i naklejkę z kodem QR; strona PDF ma format A4.
4. Plik SVG plakatu nie zawiera osadzonych bitmap ani odwołań do krojów.
5. Pary kolorów użyte na plakacie mają kontrast WCAG podany w księdze.
6. `brand/README.md` wymienia hasło dla dysponentów i pliki plakatu.
7. Pliki w `brand/logo/` i `brand/naklejka-qr/` są bez zmian
   (`git diff --stat origin/main -- brand/logo brand/naklejka-qr` jest puste).
8. Nowe i zmienione pliki nie zawierają prywatnych danych: ścieżek lokalnych,
   nazw kont, adresów e-mail (tekst, `strings` na plikach binarnych, `pdfinfo`).

## Verification

- Polecenia z punktów 1, 3, 4, 7 i 8 oraz przegląd każdej wyrenderowanej
  strony księgi i plakatu.
- Bramka repozytorium: polecenia z `validation.commands`
  w `.ai/agentic.config.json`. Test portalu w Dockerze wykonuje kontrola CI
  `validation gate`; lokalnie nie jest uruchamiany, bo projekt Compose ma
  stałą nazwę i użyłby stosu należącego do innego zadania.
- QA: zmiana obejmuje tylko dokumenty i zasoby, więc `skip-qa`.
- Ograniczenia dowodu: księga i plakat powstają z lokalnego skryptu, który
  nie jest częścią repozytorium; kolory w druku nie były sprawdzane.

## Progress

- [x] 1. Strony "Hasła" i "Plakat dla dysponentów" w księdze znaku, wersja 1.1 - 74479d9
- [x] 2. Wzór plakatu w `brand/plakat/` (SVG, PDF, PNG) - 74479d9
- [x] 3. `brand/README.md` - 74479d9
- [x] 4. Bramka walidacji i PR (cztery polecenia lokalnie; test portalu i cała bramka w kontroli CI na PR)
