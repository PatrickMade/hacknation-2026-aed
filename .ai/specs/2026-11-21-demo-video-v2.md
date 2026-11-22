# Nagranie demo Mapa Serc - wersja 2 (montaż)

Issue: APP-54
Source doc: .ai/specs/2026-11-21-demo-video-v2.md
Route: agreed delivery (small change)

## Problem

Wersja 1 nagrania (`submission/mapa-serc-demo.mp4`, APP-50) to 1 min 42 s
zrzutu ekranu w 720p z napisem wstrzykniętym w stronę: bez tytułu, znaku
akcji, dźwięku i pliku napisów. Jury ogląda je bez kontekstu, więc nagranie
musi samo pokazać problem, działający prototyp i wezwanie do działania.

## Outcome

Zmontowane nagranie zastępuje wersję 1 pod tą samą ścieżką:

- najwyżej 2:00, 1920x1080, H.264, z muzyką i bez lektora (decyzja autora
  z 2026-11-22: muzyka wygenerowana w Suno na jego koncie w planie Pro);
- napisy po polsku wypalone w obrazie oraz ten sam tekst w pliku `.srt`;
- identyfikacja Mapa Serc z `brand/` (znak, kolory, krój Figtree);
- kolejność: problem (rozproszone dane o AED) -> dysponent publikuje
  w kreatorze -> Raport zbiorczy z mapą i API -> zgłoszenie z kodu QR do
  dysponenta -> strona akcji -> wezwanie do działania;
- ujęcia portalu to nagrania ekranu lokalnej instancji z bieżącego `main`,
  a montaż powstaje w DaVinci Resolve Studio;
- teksty w pierwszej osobie liczby pojedynczej albo bezosobowo, bez twierdzeń
  wykraczających poza to, co prototyp robi.

## Scope

- `submission/mapa-serc-demo.mp4` - nowa wersja nagrania.
- `submission/mapa-serc-demo.srt` - napisy.
- `submission/nagranie-demo.md` - notatka montażowa: narzędzia, ujęcia,
  źródła i licencje, zakres użycia AI, sposób sprawdzenia.
- Wiersze o nagraniu w `submission/README.md`, `submission/lista-kontrolna.md`,
  `submission/akceptacja.md` i `submission/oswiadczenie-ai.md`.

Non-goals: zmiany kodu portalu, zmiany prezentacji PDF, lektor (także
syntetyczny), publikacja nagrania poza repozytorium, pliki projektu Resolve
i materiały robocze w repozytorium.

## Acceptance

1. `ffprobe`: strumień wideo H.264, 1920x1080, czas trwania najwyżej 120 s;
   strumień audio obecny.
2. `submission/mapa-serc-demo.srt` parsuje się (kolejne numery, rosnące czasy,
   brak nakładania), a czas ostatniego napisu mieści się w nagraniu.
3. Teksty napisów wypalonych w obrazie pochodzą z tej samej listy co `.srt`
   (jedno źródło w skrypcie montażowym); kontrola wzrokowa klatek.
4. Każda liczba i każde twierdzenie w nagraniu ma pokrycie w ujęciu ekranu
   albo w plikach repozytorium (`backend/data/aed/sources/`, `aed-standard/`).
5. Brak form pierwszej osoby liczby mnogiej w napisach i w notatce
   (grep z `.ai/specs/2026-11-21-submission-pack.md`, punkt 5).
6. Pochodzenie muzyki i podstawa jej użycia są opisane w notatce,
   a plansza końcowa podaje, że muzykę wygenerowano w Suno.
7. Jedna niezależna recenzja w roli jurora (efekt, jasność, zgodność z
   faktami, wrażenie "zrobione przez AI") i naniesione poprawki.
8. Bramka `validation.commands` przechodzi; diff dotyka tylko `submission/`
   i tej specyfikacji.

## Verification

- `ffprobe -v error -show_entries stream=codec_name,width,height:format=duration`.
- Skrypt sprawdzający `.srt` (numery, czasy, nakładanie, długość wiersza).
- Pomiar głośności (`ffmpeg ebur128`) i klatki kontrolne z gotowego pliku.
- Pełna bramka z `.ai/agentic.config.json` raz na stabilnym kandydacie.
- QA: zmiana tylko w materiałach zgłoszenia, więc `skip-qa`.

## Progress

1. [x] Issue APP-54 i claim.
2. [x] Specyfikacja (ten plik).
3. [x] Nagrania ekranu z lokalnej instancji i grafiki marki.
4. [x] Montaż w DaVinci Resolve, napisy, muzyka, eksport.
5. [x] Kontrole akceptacji, recenzja jurora i poprawki.
6. [x] Ponowne nagranie na świeżej instancji z `main` 8dcdf64 (po APP-57 i
   zmianie liczników strony akcji): 44 pola, raport bez zasobu OSM, cztery
   instytucje demonstracyjne pominięte na planszy otwierającej.
7. [x] Niezależny przegląd (CHANGES_REQUESTED na ab0d65d): poprawione napisy
   o pustych polach, e-mailu, API i Warszawie, ciaśniejsze obwódki; końcowe
   nagranie z `main` 3c108cc (dane demonstracyjne liczone osobno, dysponent
   wpisywany w kreatorze, znak z hasłem na karcie urządzenia).
8. [ ] Bramka walidacji, przegląd różnicowy, merge gate.
