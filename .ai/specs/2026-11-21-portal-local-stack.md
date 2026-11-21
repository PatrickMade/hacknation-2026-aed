# Lokalny portal dane.gov.pl dla jury
Issue: APP-42

## Cel i obecny stan
Repozytorium zawiera szkielet Flutter. Jury potrzebuje oficjalnego portalu uruchamianego lokalnie z kodu, wraz z kontami demonstracyjnymi. Zastępujemy szkielet oficjalnymi wydaniami backend 2.62.3 i frontend 3.5.2 na GPLv3.

## Zakres
Źródła w backend/ i frontend/, jedna konfiguracja compose.yaml i opisana sekwencja budowy, migracji, seedowania oraz startu. Zachowujemy oryginalne notices i dołączamy oficjalną licencję, pochodzenie, SHA-256 archiwów oraz datowaną listę zmian. Zmieniamy tylko konfigurację lokalną i telemetrię. Nie zmieniamy designu, treści ani układu portalu. Seed tworzy instytucje i konta, bez zbiorów AED i bez nowych stron CMS. Flutter usuwamy po potwierdzeniu startu portalu z repozytorium. Aktualizujemy README, AGENTS, SDLC i CI. Konkretne wystąpienia publicznych przykładów i certyfikatów testowych upstream są zapisane w .gitleaksignore; ich oryginalne pliki nadal muszą przejść kontrolę SHA-256.

## Ustalenia
- Web lokalny jest jedynym celem tej zmiany; brak publikacji produkcyjnej i wydania mobilnego.
- Istniejąca rola administratora portalu to is_superuser; tworzymy oddzielne konto bootstrap superadmina oraz konto administratora. Nie wprowadzamy nowego modelu ról.
- Sześć instytucji: Krosno, Marki, Przemyśl, Warszawa, Legionowo, Dysponent demonstracyjny. Każda ma osobne konto pełnomocnika i edytora. Łącznie 15 kont: dwa administracyjne, 12 instytucjonalnych i zwykły użytkownik.
- Hasła są wymagane w ignorowanym .env. Przykład nie zawiera wartości haseł. Seed nie wypisuje haseł, nie tworzy duplikatów, waliduje komplet konfiguracji przed zapisem i przypisuje twórcę instytucji do bootstrap superadmina.
- Start nie ładuje upstream basic_data.json z publicznymi hasłami i przykładowym zbiorem. Wykorzystuje migracje i własny seed kont. Brak stron CMS jest ograniczeniem oficjalnego pustego wdrożenia, bez dodawania treści zastępczych.

## Kryteria akceptacji i weryfikacja
1. Oficjalne źródła i licencja: porównanie zawartości archiwów, sum i listy modyfikacji; brak nieopisanych zmian UI.
2. Compose: config --quiet przechodzi z przykładem env; build i start usług z repozytorium; API, publiczny frontend, admin i CMS odpowiadają.
3. Seed: dwukrotne uruchomienie zachowuje identyfikatory i liczby 6 instytucji/15 kont; brak wymaganych haseł przerywa bez zapisu. Logowanie kont i odmowa dostępu edytora do obcej instytucji oraz użytkownika do panelu są sprawdzone wykonaniem testu Django.
4. Telemetria: Sentry, Matomo i flagi nie wysyłają danych na produkcyjne endpointy w lokalnym uruchomieniu. Konfigurację kontrolują testy i obserwacja żądań w przeglądarce.
5. Polska instrukcja startu opisuje env, hosts, certyfikaty, komendy, loginy bez haseł i zatrzymanie z zachowaniem danych. Zależności/budowa wymagają Internetu i emulacji amd64 na arm64.
6. Flutter znika po sprawdzeniu startu; nowa bramka CI sprawdza konfigurację, testy seedowania i zachowanie kopii harnessu/pinów. Pełny gate przechodzi, niezależny review obejmuje spec i kod, merge przez merge_gate.py.

## Ryzyka i granice
Portal ma stare zależności; ta zmiana nie modernizuje ich ani nie nadaje się do wdrożenia publicznego. Pusta baza nie odtwarza treści produkcyjnych CMS. Lokalny certyfikat wymaga świadomej akceptacji w przeglądarce. Stack badawczy zostanie zatrzymany przed startem własnego, z zachowaniem wolumenów. Kontenery nowego projektu i wolumeny są odrębne. Hasła oraz klucze mają być generowane lokalnie; nie są częścią obrazu ani Git.

## Poza zakresem
Funkcje i dane AED, branding, zmiany treści i layoutu, produkcja oraz hosting publiczny.

## Plan wdrożenia
1. Zaimportować źródła, pochodzenie i licencję; przygotować Compose i konfigurację lokalną.
2. Test RED wymaganej zawartości seedowania, potem seed i GREEN; potwierdzić powtórzenie, uprawnienia i brak haseł.
3. Zatrzymać badawczy stack; zbudować i uruchomić własny; sprawdzić HTTP i przeglądarkę.
4. Usunąć Flutter, zaktualizować dokumentację i gate CI; uruchomić pełny gate, niezależny review i merge.

## Przygotowanie runnera CI

Pełna budowa na jednorazowym runnerze GitHub Actions wymaga usunięcia preinstalowanego, nieużywanego przez portal Android SDK z /usr/local/lib/android przed budową. Zaobserwowano ENOSPC podczas pierwszej budowy. Zmiana dotyczy wyłącznie efemerycznego runnera workflow ubuntu-latest; wszystkie obrazy i validation.commands nadal są wymagane.

Compose definiuje pięć usług aplikacji z jednym wspólnym obrazem. Budujemy każdy unikalny obraz raz. CI wykonuje budowy kolejno i usuwa wyłącznie cache BuildKit na jednorazowym runnerze między obrazami; obrazy wynikowe i wszystkie kontrole pozostają zachowane.
