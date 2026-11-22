from django import forms
from django.utils import timezone

from mcod.aed_wizard import mapping, standard
from mcod.aed_wizard.publish import LICENSES
from mcod.datasets.models import UPDATE_FREQUENCY

NOT_MAPPED = ("", "- nie przypisuj -")


class SourceForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=None, label="Instytucja (dysponent AED)", empty_label=None)
    file = forms.FileField(
        label="Plik CSV, XLSX lub GeoJSON", required=False,
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx,.geojson,.json"}),
    )
    url = forms.URLField(label="albo adres URL pliku", required=False)

    def __init__(self, organizations, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organization"].queryset = organizations

    def clean(self):
        data = super().clean()
        if bool(data.get("file")) == bool(data.get("url")):
            raise forms.ValidationError("Wgraj plik albo podaj adres URL (jedno z dwóch).")
        return data


class CheckForm(forms.Form):
    file = forms.FileField(
        label="Plik CSV, XLSX lub GeoJSON (do 10 MB)",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx,.geojson,.json"}),
    )


def enum_choices(name):
    field = next(field for field in standard.fields() if field["name"] == name)
    return [(value, value) for value in field["constraints"]["enum"]]


class MappingForm(forms.Form):
    """One select per profile target, defaults for required fields, licence and data date."""

    def __init__(self, columns, organization, *args, detected_date=(None, None), **kwargs):
        super().__init__(*args, **kwargs)
        suggested = mapping.suggest(columns)
        choices = [NOT_MAPPED] + [(column, column) for column in columns]
        self.target_names = []
        for target, label in mapping.targets():
            name = "map_" + target
            self.fields[name] = forms.ChoiceField(
                label=label, choices=choices, required=False, initial=suggested.get(target, "")
            )
            self.target_names.append(name)
        self.default_names = []
        titles = {field["name"]: field.get("title", field["name"]) for field in standard.fields()}
        for field, value in mapping.DEFAULTS.items():
            name = "default_" + field
            self.fields[name] = forms.ChoiceField(label="{} ({})".format(titles[field], field),
                                                  choices=enum_choices(field), initial=value)
            self.default_names.append(name)
        self.fields["operator_name"] = forms.CharField(
            label="Dysponent (operator_name), gdy brak kolumny", initial=organization.title, max_length=300
        )
        self.fields["license"] = forms.ChoiceField(
            label="Licencja danych", choices=[(key, value[2]) for key, value in LICENSES.items()], initial="cc0",
            widget=forms.RadioSelect,
        )
        day, origin = detected_date
        self.fields["data_date"] = forms.DateField(
            label="Data danych (RRRR-MM-DD)", initial=day,
            help_text=("Wykryto w pliku (pole {}). Zmień, jeśli dane dotyczą innego dnia.".format(origin) if day else
                       "Plik nie zawiera daty danych. Wpisz dzień, którego dotyczą dane, np. datę ostatniej "
                       "aktualizacji ewidencji AED."),
            error_messages={"required": "Podaj datę danych: dzień, którego dotyczą dane w pliku."},
            widget=forms.DateInput(attrs={"type": "date", "aria-describedby": "data-date-help"}, format="%Y-%m-%d"),
        )
        self.fields["swap_axes"] = forms.BooleanField(
            label="Zamień szerokość i długość w wierszach z prawdopodobnie zamienionymi osiami", required=False
        )

    def clean_data_date(self):
        day = self.cleaned_data["data_date"]
        if day > timezone.localdate():
            raise forms.ValidationError("Data danych nie może być późniejsza niż dzisiaj.")
        return day

    def target_fields(self):
        return [self[name] for name in self.target_names]

    def default_fields(self):
        return [self[name] for name in self.default_names]

    def mapping(self):
        return {name[4:]: self.cleaned_data[name] for name in self.target_names if self.cleaned_data.get(name)}

    def defaults(self):
        return {name[8:]: self.cleaned_data[name] for name in self.default_names}


class PublishForm(forms.Form):
    title = forms.CharField(label="Tytuł zasobu", max_length=300)
    description = forms.CharField(label="Opis zasobu (opcjonalnie)", required=False,
                                  widget=forms.Textarea(attrs={"rows": 3}))
    update_frequency = forms.ChoiceField(
        label="Częstotliwość aktualizacji",
        choices=[choice for choice in UPDATE_FREQUENCY if choice[0] != "notApplicable"], initial="monthly",
    )
