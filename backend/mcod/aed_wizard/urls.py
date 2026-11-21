from django.urls import path

from mcod.aed_wizard import views

app_name = "aed_wizard"
urlpatterns = [
    path("kreator/", views.source, name="source"),
    path("kreator/kolumny/", views.mapping_step, name="mapping"),
    path("kreator/raport/", views.report, name="report"),
    path("kreator/raport/aed-standard.csv", views.converted_csv, name="converted_csv"),
    path("kreator/opublikowano/", views.done, name="done"),
    path("sprawdz-plik/", views.check, name="check"),
    path("standard/<str:name>", views.download_standard_file, name="standard_file"),
]
