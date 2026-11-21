# Ograniczenia prototypu

Wersja 1 (2026-11-21). Lista zostanie uzupełniona po scaleniu modułów AED
o ograniczenia stwierdzone w ich testach.

## Środowisko i publikacja

1. Prototyp działa w **lokalnej instancji** portalu dane.gov.pl (Docker
   Compose). Nie ma publicznego hostingu; jury uruchamia go z kodu, a dowody
   działania są na zrzutach ekranu i w nagraniu demo.
2. W produkcyjnym dane.gov.pl niczego nie opublikowano. Ścieżka publikacji
   (instytucja, zbiór, zasób, panel dostawcy) jest ta sama, ale wymaga kont
   dysponentów i zgody operatora portalu.
3. Lokalny portal ma dane startowe z kodu portalu i własne konta demo, bez
   treści CMS z produkcji. Strony CMS, których nie ma w danych startowych,
   zwracają 404.
4. Część obrazów usług portalu powstała dla architektury amd64. Na
   komputerach z procesorem ARM (np. Apple Silicon) działają w emulacji,
   więc pierwsze uruchomienie trwa dłużej.
5. Publiczne API portalu (`/1.4`) służy do odczytu. Publikacja odbywa się
   przez panel dostawcy albo mechanizm importu (harvester), a nie przez
   ogólne API zapisu.

## Dane

6. Dane w demo to migawki pięciu istniejących zbiorów AED z dane.gov.pl
   (Krosno, Marki, Przemyśl, Warszawa, Legionowo) z adresem źródła i datą
   pobrania. Nie są aktualizowane na żywo z produkcji.
7. Dla Warszawy nie potwierdzono metody i struktury odpowiedzi API z danymi
   AED; mapowanie tego zbioru jest oznaczone jako niepotwierdzone.
8. Wpisy ze stron gov.pl i BIP (739 wpisów z 20 źródeł, w tym 137 ze
   współrzędnymi) służą tylko jako **oznaczone dane demonstracyjne**. Warunki
   ponownego wykorzystania części stron gminnych nie są rozstrzygnięte.
9. Żaden rekord nie potwierdza fizycznego istnienia, sprawności ani
   aktualnej dostępności AED. Nie przeprowadzono oględzin ani weryfikacji
   u dysponentów.
10. Punkty AED z OpenStreetMap są osobnym zasobem na licencji ODbL 1.0.
    Selektor licencji w obecnym kodzie portalu nie zawiera ODbL; sposób
    publikacji takiego zasobu na produkcji trzeba uzgodnić z operatorem
    portalu. Dane OSM nie wskazują odpowiedzialnego dysponenta.

## Jakość danych i walidacja

11. Wzorcowy zakres danych to propozycja przygotowana na potrzeby zadania,
    a nie obowiązujący standard państwowy.
12. Walidator sprawdza strukturę, typy, wymagane pola, słowniki, reguły
    między polami i orientacyjną ramkę Polski (48,9-55,1 N, 14-24,2 E).
    Nie sprawdza granic administracyjnych, istnienia kodu w rejestrze TERYT,
    pełnej gramatyki `opening_hours` ani braku danych osobowych w dowolnym
    tekście.

Punkty 13-17 opisują założenia modułów AED, które są w realizacji
[do uzupełnienia: potwierdzić po scaleniu modułów i ich testach].

13. Deduplikacja wskazuje kandydatów do scalenia. Wspólny adres lub
    współrzędne nie dowodzą, że dwa rekordy opisują to samo urządzenie.
14. Wbudowana mapa portalu czyta dane tabelaryczne. Zasób GeoJSON jest
    do pobrania, bez podglądu na mapie.
15. Odświeżanie raportu zbiorczego jest zaprojektowane jako codzienne
    zadanie w tle; w demo uruchamia się je ręcznie.

## Zgłoszenia problemów

16. Formularz zgłoszenia nie zastępuje numeru alarmowego 112 i nie gwarantuje
    czasu reakcji dysponenta.
17. Powiadomienia e-mail w demo trafiają do lokalnej skrzynki testowej
    (MailHog), a nie do prawdziwych adresów.

## Dostępność i zakres zmian

18. Wymagania WCAG 2.2 AA i responsywności (od 360 px) dotyczą nowych stron
    AED. Pozostała część portalu jest bez zmian i poza zakresem audytu.
19. Kod portalu pochodzi z oficjalnego wydania (backend 2.62.3, frontend
    3.5.2) na licencji GPLv3. Zmiany i moduły AED podlegają tej samej
    licencji [do uzupełnienia: plik licencji i opis zmian po scaleniu
    konfiguracji portalu].
