# Informacja o wolnym pierwszym otwarciu strony
Issue: APP-72

## Problem
Końcowe QA integracyjne na `main` fc042867: na świeżym stacku pierwsze otwarcie `/pl/aed` trwało 49-90 s, bo serwer deweloperski Angulara kompiluje trasę przy pierwszym wejściu; odświeżenie było szybkie. Juror może uznać, że portal się zawiesił.

## Zmiana
README: przy sprawdzeniu gotowości frontendu zdanie, że pierwsze otwarcie każdej strony (np. `/pl/aed`) może trwać 1-2 minuty i że przy pustych licznikach trzeba odświeżyć stronę; w kroku 1 sekcji „Demo w 10 minut” krótka uwaga w tej samej linii.

## Kryteria akceptacji i weryfikacja
1. Oba zdania są w README w opisanych miejscach (przegląd diffu).
2. Pełna bramka `validation.commands` przechodzi; niezależny review; merge przez `merge_gate.py`.

## Poza zakresem
Zmiana serwera deweloperskiego lub wstępna kompilacja frontendu.
