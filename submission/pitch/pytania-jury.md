# Mapa Serc - prawdopodobne pytania jury i odpowiedzi

Odpowiedzi są krótkie, do powiedzenia w 20-30 sekund. Liczby i stan
prototypu według `main` z 22.11.2026. Pełna lista ograniczeń:
`submission/ograniczenia.md`.

## Zgodność z dane.gov.pl

**1. Dlaczego moduł w portalu, a nie osobna aplikacja?**
Bo dane.gov.pl ma już to, czego potrzeba: instytucje, konta pełnomocników,
zbiory, zasoby, licencje, mapę i API. Dodałem 3 moduły do oficjalnego kodu
portalu (backend 2.62.3, frontend 3.5.2, GPLv3). Operator niczego nie
buduje od zera i nie utrzymuje drugiego systemu.

**2. Czy to działa na produkcyjnym dane.gov.pl?**
Nie. To lokalna kopia portalu uruchamiana z Docker Compose. Na produkcji
niczego nie opublikowałem. Do wdrożenia potrzeba decyzji operatora
i włączenia modułów na środowisku testowym portalu.

**3. Skąd pochodzą dane i jak są aktualizowane?**
Raport czyta pięć istniejących zbiorów AED z publicznego API dane.gov.pl:
Krosno, Marki, Przemyśl, Legionowo i Warszawę (Warszawa ma tylko metadane,
dane są za kluczem miejskiego API). Odświeżanie działa codziennie o 03:30
UTC; gdy API nie odpowiada, raport używa datowanej kopii i zapisuje to
w opisie zbioru. Ograniczenie: identyfikatory zasobów źródłowych są
wpisane w kod, więc po podmianie pliku przez urząd trzeba je poprawić.

**4. Co z licencjami?**
Raport jest na CC BY 4.0, a każdy rekord niesie licencję swojego źródła
(CC0 1.0 albo CC BY 4.0). Punkty z OpenStreetMap są osobnym zbiorem
z tekstem ODbL 1.0. Słownik licencji portalu nie ma ODbL, więc etykieta
odczytywana maszynowo pokazuje tam CC BY 4.0. To wymaga decyzji operatora
i mówię o tym wprost w załączniku A prezentacji.

**5. Czy dane są maszynowo czytelne i na ile otwarte?**
CSV, GeoJSON, JSON-LD i JSON z API portalu; metadane zbioru w RDF ze
słownikami DCAT. Zasób CSV ma w portalu 4 z 5 gwiazdek otwartości.

**6. Co z dostępnością (WCAG)?**
Automatyczna kontrola axe-core nie wykazała naruszeń w treści nowych
ekranów AED, także przy szerokości 360 px. Trzy uwagi dotyczą
niezmienionej powłoki portalu. Nie robiłem testu z czytnikiem ekranu.

## Dane i wzorcowy zakres

**7. Co zawiera wzorcowy zakres danych?**
44 pola, w tym 15 wymaganych i 3 warunkowe: identyfikacja, miejsce
z kodami TERYT, dostępność, stan urządzenia i dysponent, pochodzenie
i oznaczenia jakości. Jest słownik XLSX, schemat Table Schema, szablon
CSV i walidator z testami. To propozycja, nie obowiązujący standard.

**8. Dlaczego w danych jest tyle wartości "unknown"?**
Bo pliki miast nie podają dostępu, stanu urządzenia ani umieszczenia
w budynku. W 74 rekordach z plików miast sześć z 15 pól wymaganych ma
wartość "unknown". Nie zgaduję brakujących wartości; zakres wymaga, żeby
brak wiedzy był zapisany jawnie.

**9. Kto jest dysponentem w rekordach z plików miast?**
Instytucja nazwana w pliku miasta, a gdy plik jej nie nazywa, urząd
miasta. Każdy taki rekord ma oznaczenie, że dysponent nie jest
potwierdzony. Potwierdzony dysponent to ten, kto sam opublikował dane
w kreatorze; w demo są to 4 fikcyjne instytucje.

**10. Jak wykrywane są błędy i duplikaty?**
Walidator sprawdza strukturę, typy, pola wymagane i słowniki. Agregator
naprawia zamienione współrzędne (7 par w pliku Marek), sprawdza, czy punkt
leży w granicach gminy według PRG, i oznacza możliwe duplikaty: rekordy
bliżej niż 25 m scala tylko przy tej samej nazwie i adresie, w innym
razie oznacza je do sprawdzenia (4 rekordy).

**11. Dlaczego punkty z OpenStreetMap nie są w raporcie?**
Bo mają inną licencję (ODbL) i nie mają potwierdzonego dysponenta. Służą
do porównania: pokazują 2124 gminy, w których wolontariusze zaznaczyli
AED, a dane.gov.pl nie ma o nich danych.

**12. Ile danych jest prawdziwych, a ile demonstracyjnych?**
74 rekordy pochodzą z prawdziwych plików czterech miast. 12 rekordów
i 4 instytucje są fikcyjne i tak oznaczone; pokazują publikację przez
kreator. Strona akcji liczy je osobno.

## Użytkownicy i wdrożenie

**13. Jak dane opublikuje firma albo wspólnota bez konta w portalu?**
Prototyp nie dodaje dla niej nowej funkcji. Są dwie drogi dostępne już
dziś: wniosek o konto dostawcy w dane.gov.pl albo przekazanie danych
gminie, która publikuje je w swoim zbiorze.

**14. Jak skorzysta z tego dyspozytor 112 albo ratownik?**
Dziś przez API portalu i mapę z filtrem odległości ("Najbliższy AED").
Podłączenie do systemu dyspozytorskiego jest poza prototypem. Warunkiem
jest najpierw wiarygodny zbiór, i to on jest przedmiotem tej pracy.

**15. Co się dzieje ze zgłoszeniem z kodu QR?**
Trafia do panelu instytucji, która odpowiada za dane tego urządzenia,
i na jej e-mail. Formularz nie wymaga danych osobowych. Podpis i kontakt,
jeśli ktoś je poda, są usuwane 30 dni po rozwiązaniu zgłoszenia. Formularz
nie zastępuje numeru 112. Brakuje jeszcze limitu zgłoszeń z jednego
adresu, a treść klauzuli informacyjnej wymaga weryfikacji prawnej.

**16. Co trzeba zrobić, żeby to wdrożyć?**
Trzy kroki: operator włącza moduły AED na testowym środowisku portalu;
Krosno, Marki, Przemyśl i Legionowo publikują przez kreator i proszą
instytucje ze swoich plików o potwierdzenie danych; prawnicy portalu
rozstrzygają publikację punktów OSM na ODbL i treść klauzuli.

**17. Jak zachęcić dysponentów?**
Mapa luk daje listę gmin do zaproszenia, od największych: Warszawa,
Wrocław, Kraków, Poznań, Gdańsk. Akcja ma do nich własne hasło, wzór
plakatu i naklejkę. Dysponent dostaje oznaczenie zgodności przy zasobie
i zieloną gminę na mapie.

## Znak i hasło

**18. Czy znak nie myli się z oznaczeniem AED?**
Nawiązanie jest celowe: serce z błyskawicą to motyw rozpoznawany na całym
świecie. Znak akcji wpisuje je w kontur Polski i oznacza akcję oraz jej
mapę, a nie miejsce urządzenia. Księga znaku mówi to wprost: znak nie
zastępuje znaku AED. Naklejka przy urządzeniu ma swój wzór do druku
z wierszem o numerze 112.

**19. "Wszystkie AED pod ręką" przy 74 rekordach?**
To cel akcji, nie opis stanu. Stan pokazują liczniki i mapa luk na
stronie akcji. Dla dysponentów jest drugie hasło, które mówi o ich roli:
"Lista AED w szufladzie nikogo nie uratuje."

## Praca i jakość

**20. Jaki był udział AI?**
Kod modułów, wzorcowy zakres danych, pliki znaku, prezentację i nagranie
przygotowały narzędzia AI (Claude Code, Codex). Decyzje należały do mnie:
moduł wewnątrz portalu, raport zbiorczy, punkty OSM jako osobny zbiór,
nazwa, hasła i wariant znaku. Dane o prawdziwych urządzeniach pochodzą
tylko z plików urzędów i z OpenStreetMap. Szczegóły:
`submission/oswiadczenie-ai.md`.

**21. Skąd pewność, że kod działa?**
Każda zmiana przeszła bramkę w CI, w tym 93 testy automatyczne modułów
AED i kont demonstracyjnych, oraz niezależny przegląd w osobnej sesji.
Portal uruchamia się z repozytorium według README; każdy może to
powtórzyć.

**22. Co jest największą słabością rozwiązania?**
Wiarygodność danych: żaden rekord nie potwierdza, że urządzenie istnieje
i działa, a dysponenci rekordów z plików miast nie są potwierdzeni.
Mechanizm to umożliwia (publikacja przez dysponenta, zgłoszenia z kodu
QR), ale potwierdzeń jeszcze nie ma.
