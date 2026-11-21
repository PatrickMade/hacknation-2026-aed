# Misja AED - Dane na ratunek

Prototyp na HackNation 2026 (wyzwanie Ministerstwa Cyfryzacji, Departament Zarządzania Danymi).
Rozwiązanie zbiera dane o defibrylatorach AED z rozproszonych źródeł do jednego otwartego
zbioru w formacie maszynowym, zgodnego z zasadami portalu dane.gov.pl.

Aplikacja Flutter: web (główny prototyp dla jury) oraz iOS i Android.

## Uruchomienie

Wymagany Flutter z `.fvmrc` (przez [FVM](https://fvm.app)).

```bash
fvm flutter pub get
fvm flutter run -d chrome
```

## Sprawdzenie

```bash
fvm flutter analyze
fvm flutter test
```
