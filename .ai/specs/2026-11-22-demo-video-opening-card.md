# Nagranie demo - zdanie o OpenStreetMap na planszy otwierającej

Issue: APP-73
Source doc: .ai/specs/2026-11-22-demo-video-opening-card.md
Route: agreed delivery (small change)
Extends: `.ai/specs/2026-11-21-demo-video-v2.md` (APP-54)

## Problem

Plansza otwierająca `submission/mapa-serc-demo.mp4` mówi "W 2124 gminach AED
zna tylko OpenStreetMap." Zdanie sugeruje, że nikt poza OpenStreetMap nie wie
o tych urządzeniach. Autor odrzucił to sformułowanie już w prezentacji
(slajd 7).

## Outcome

Plansza i `submission/mapa-serc-demo.srt` mówią to samo co slajd 7
prezentacji: "W 2124 gminach wolontariusze OpenStreetMap zaznaczyli AED,
a dane.gov.pl nie ma o nich danych." Żaden inny napis ani plansza nie używa
zwrotów "zna tylko" ani "tylko OpenStreetMap". Plansza trwa o 1 s dłużej,
żeby dało się ją przeczytać.

Dwie poprawki napisów zatwierdzone przez autora w tym samym renderze:

- tabela: "Brak danych: „unknown” w polu wymaganym, puste pole
  w opcjonalnym." (kadr pokazuje `unknown` w polach słownikowych); ujęcie
  trwa o 1 s dłużej;
- liczniki strony akcji: "Dane demonstracyjne są liczone osobno. Krosno
  opublikowało dane w kreatorze: stąd 9 wydawców."

## Scope

- `submission/mapa-serc-demo.mp4` - nowy render z istniejących ujęć: grafika
  planszy otwierającej, dwa napisy, plansza i ujęcie tabeli dłuższe o 1 s.
- `submission/mapa-serc-demo.srt` - te same teksty.
- `submission/nagranie-demo.md` i wiersze o nagraniu - czas trwania, rozmiar
  pliku i tabela czasów.

Non-goals: ponowne nagrania ekranu, nowa plansza z odpowiedzią API, zmiany
prezentacji.

## Acceptance

1. Klatki planszy otwierającej pokazują nowe zdanie, czytelne i mieszczące się
   w kadrze.
2. `git grep "zna tylko\|tylko OpenStreetMap" -- submission` nie znajduje nic.
3. `ffprobe`: H.264, 1920x1080, jeden strumień audio, czas najwyżej 120 s
   (poprzednia wersja 116,8 s, nowa o 2 s dłuższa).
4. Bramka `validation.commands` przechodzi; diff dotyka tylko `submission/`
   i tej specyfikacji.

## Progress

1. [x] Issue APP-73 i claim.
2. [x] Grafika planszy, render z istniejących ujęć, kontrola klatek.
3. [ ] Bramka walidacji, PR, niezależny przegląd, merge gate.
