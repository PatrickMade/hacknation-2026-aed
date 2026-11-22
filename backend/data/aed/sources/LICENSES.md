# Licencje danych źródłowych AED

Pliki w tym katalogu to datowane kopie danych zewnętrznych, pobrane
2026-11-21T17:32:40Z (UTC). Nie są objęte licencją GNU GPL v3.0 repozytorium.
Każdy plik zachowuje licencję i warunki swojego źródła.

| Katalog | Źródło | Licencja | Uznanie autorstwa |
|---|---|---|---|
| `krosno/` | Urząd Miasta Krosna, dane.gov.pl zbiór 3624 (https://dane.gov.pl/pl/dataset/3624) | CC0 1.0 | nie jest wymagane |
| `marki/` | Urząd Miasta Marki, dane.gov.pl zbiór 4955 (https://dane.gov.pl/pl/dataset/4955) | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) | "Urząd Miasta Marki, dane.gov.pl zbiór 4955" |
| `przemysl/` | Urząd Miejski w Przemyślu, dane.gov.pl zbiór 4581 (https://dane.gov.pl/pl/dataset/4581) | CC0 1.0 | nie jest wymagane |
| `warszawa/` | Urząd m.st. Warszawy, dane.gov.pl zbiór 39512 (https://dane.gov.pl/pl/dataset/39512), tylko metadane | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) | "Urząd m.st. Warszawy, dane.gov.pl zbiór 39512" |
| `legionowo/` | Urząd Miasta Legionowo, dane.gov.pl zbiór 40593 (https://dane.gov.pl/pl/dataset/40593) | CC0 1.0 | nie jest wymagane |
| `osm/PL.geojson.gz` | OpenStreetMap, eksport krajowy OpenAEDMap (https://openaedmap.org/api/v1/countries/PL.geojson) | Open Database License 1.0 (https://opendatacommons.org/licenses/odbl/1-0/) | "© OpenStreetMap contributors" |

Pliki `dataset.json`, `resources.json` i `institution.json` to metadane z API
dane.gov.pl (https://api.dane.gov.pl/1.4/) opisujące te zbiory.

Kopia OSM jest wejściem agregatora. Zasób "Punkty AED z OpenStreetMap - Polska
(ODbL 1.0)" w lokalnym portalu jest bazą pochodną: publikowany jest na ODbL 1.0
z uznaniem "© OpenStreetMap contributors", bez telefonów, e-maili i danych
autorów edycji. Licencja CC BY 4.0 zbioru "Raport zbiorczy AED" nie obejmuje
tego zasobu.

## Granice gmin (PRG)

`../prg/gminy_dysponentow.geojson` zawiera dokładne granice czterech gmin
dysponentów źródeł miejskich (Krosno 1861011, Marki 1434021, Przemyśl 1862011,
Legionowo 1408011) z Państwowego Rejestru Granic, pobrane z usługi GUGiK ULDK
(https://uldk.gugik.gov.pl/) 2026-11-21 (czas UTC w pliku). Źródło: Główny
Urząd Geodezji i Kartografii, PRG; dane udostępniane przez GUGiK bez opłat.
To ten sam rejestr, z którego pochodzą uproszczone granice strony akcji
(`frontend/src/assets/aed/gminy.geojson`).
