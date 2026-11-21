import csv
import datetime
import io
import uuid

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from mcod.aed_wizard import mapping, readers, standard
from mcod.aed_wizard.forms import CheckForm, MappingForm, PublishForm, SourceForm
from mcod.aed_wizard.publish import LICENSES, mark, publish
from mcod.organizations.models import Organization

SESSION_KEY = "aed_wizard_token"
STATE_TTL = 3600
DOWNLOADS = {
    "template.csv": "text/csv",
    "example.csv": "text/csv",
    "field-dictionary.xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
PREVIEW_ROWS = 5


def organizations_for(user):
    if user.is_superuser:
        return Organization.objects.filter(is_removed=False).order_by("title")
    return user.organizations.filter(is_removed=False).order_by("title")


def wizard_view(view):
    @staff_member_required
    @never_cache
    def wrapper(request, *args, **kwargs):
        if not organizations_for(request.user).exists():
            raise PermissionDenied("Kreator jest dostępny dla kont przypisanych do instytucji.")
        return view(request, *args, **kwargs)

    wrapper.__name__ = view.__name__
    return wrapper


def load_state(request):
    token = request.session.get(SESSION_KEY)
    state = cache.get("aed_wizard:" + token) if token else None
    if not state or state["user"] != request.user.pk:
        return None
    if not organizations_for(request.user).filter(pk=state["organization"]).exists():
        raise PermissionDenied("Brak uprawnień do tej instytucji.")
    return state


def save_state(request, state):
    token = request.session.get(SESSION_KEY) or uuid.uuid4().hex
    request.session[SESSION_KEY] = token
    cache.set("aed_wizard:" + token, state, STATE_TTL)


def context(request, step, **extra):
    data = admin.site.each_context(request)
    data.update({"step": step, "title": "Dodaj dane AED", "standard_version": standard.version()})
    data.update(extra)
    return data


def download_standard_file(request, name):
    if name not in DOWNLOADS:
        raise Http404()
    path = standard.standard_dir() / name
    return FileResponse(open(str(path), "rb"), as_attachment=True, filename=name, content_type=DOWNLOADS[name])


@wizard_view
def source(request):
    organizations = organizations_for(request.user)
    form = SourceForm(organizations, request.POST or None, request.FILES or None)
    error = None
    if request.method == "POST" and form.is_valid():
        try:
            if form.cleaned_data["file"]:
                upload = form.cleaned_data["file"]
                name, source_url = upload.name, ""
                table = readers.read(name, upload.read(readers.MAX_BYTES + 1))
            else:
                source_url = form.cleaned_data["url"]
                name, data = readers.fetch(source_url)
                table = readers.read(name, data)
        except readers.SourceError as exc:
            error = str(exc)
        else:
            save_state(request, {"user": request.user.pk, "organization": form.cleaned_data["organization"].pk,
                                 "table": table.to_dict(), "source_name": name or source_url,
                                 "source_url": source_url})
            return redirect("aed_wizard:mapping")
    return render(request, "aed_wizard/source.html", context(request, 1, form=form, error=error,
                                                             downloads=list(DOWNLOADS)))


def conversion_context(organization, state, cleaned):
    source_url = state["source_url"] or "{}/pl/institution/{}".format(settings.BASE_URL, organization.pk)
    return {
        "org_slug": organization.slug,
        "operator_name": cleaned["operator_name"],
        "source_url": source_url,
        "license_url": LICENSES[cleaned["license"]][1],
        "data_date": cleaned["data_date"].isoformat(),
        "now": timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@wizard_view
def mapping_step(request):
    state = load_state(request)
    if state is None:
        return redirect("aed_wizard:source")
    organization = Organization.objects.get(pk=state["organization"])
    table = readers.Table.from_dict(state["table"])
    form = MappingForm(table.columns, organization, request.POST or None, initial=state.get("mapping_initial"))
    if request.method == "POST" and form.is_valid():
        conversion = mapping.convert(table, form.mapping(), form.defaults(),
                                     conversion_context(organization, state, form.cleaned_data),
                                     swap_axes=form.cleaned_data["swap_axes"])
        output = conversion.csv_bytes()
        state.update({
            "mapping_initial": {key: value for key, value in form.cleaned_data.items() if key != "data_date"},
            "csv": output.decode("utf-8"),
            "errors": standard.validate_bytes(output),
            "warnings": conversion.warnings,
            "records": len(conversion.records),
            "generated_ids": conversion.generated_ids,
            "columns": conversion.columns,
            "license": form.cleaned_data["license"],
            "data_date": form.cleaned_data["data_date"].isoformat(),
        })
        save_state(request, state)
        return redirect("aed_wizard:report")
    preview = table.rows[:PREVIEW_ROWS]
    return render(request, "aed_wizard/mapping.html", context(
        request, 2, form=form, organization=organization, columns=table.columns, rows_count=len(table.rows),
        preview=[[row.get(column, "") for column in table.columns] for row in preview],
        source_name=state["source_name"],
    ))


@wizard_view
def report(request):
    state = load_state(request)
    if state is None or "csv" not in state:
        return redirect("aed_wizard:source")
    organization = Organization.objects.get(pk=state["organization"])
    form = PublishForm(request.POST or None, initial={"title": "Defibrylatory AED - {} ({})".format(
        organization.title, state["data_date"])})
    if request.method == "POST" and not state["errors"] and form.is_valid():
        meta = dict(form.cleaned_data, license=state["license"], source_name=state["source_name"],
                    data_date=datetime.date.fromisoformat(state["data_date"]))
        publication = publish(organization, request.user, state["csv"].encode("utf-8"), state["records"],
                              len(state["warnings"]), meta)
        cache.delete("aed_wizard:" + request.session.pop(SESSION_KEY))
        request.session["aed_wizard_done"] = publication.pk
        return redirect("aed_wizard:done")
    preview = list(csv.reader(io.StringIO(state["csv"], newline="")))[1:PREVIEW_ROWS + 1]
    return render(request, "aed_wizard/report.html", context(
        request, 3, organization=organization, form=form, errors=state["errors"], warnings=state["warnings"],
        records=state["records"], generated_ids=state["generated_ids"], columns=state["columns"],
        license_name=LICENSES[state["license"]][2], data_date=state["data_date"], mark=mark(),
        preview=preview,
    ))


@wizard_view
def converted_csv(request):
    state = load_state(request)
    if state is None or "csv" not in state:
        raise Http404()
    response = HttpResponse(state["csv"].encode("utf-8"), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="aed-standard.csv"'
    return response


@wizard_view
def done(request):
    from mcod.aed_wizard.models import AedPublication

    publication = AedPublication.objects.filter(
        pk=request.session.get("aed_wizard_done"),
        organization_id__in=organizations_for(request.user).values("pk"),
    ).first()
    if publication is None:
        return redirect("aed_wizard:source")
    return render(request, "aed_wizard/done.html", context(
        request, 4, publication=publication, mark=mark(), base_url=settings.BASE_URL, api_url=settings.API_URL,
    ))


def table_to_profile_csv(table):
    """Public check of XLSX/GeoJSON: keep only columns named like profile fields (no guessing)."""
    names = standard.field_names()
    renamed = {readers.GEOJSON_LAT: "latitude", readers.GEOJSON_LON: "longitude"}
    columns = []
    for column in table.columns:
        target = renamed.get(column, column)
        if target in names and target not in [item[1] for item in columns]:
            columns.append((column, target))
    columns.sort(key=lambda item: names.index(item[1]))
    conversion = mapping.Conversion([target for _, target in columns],
                                    [{target: row.get(column, "") for column, target in columns} for row in table.rows],
                                    [], 0)
    return conversion.csv_bytes(), [column for column in table.columns if column not in dict(columns)]


@never_cache
def check(request):
    """Public validator: nothing is stored; the upload lives only for this request."""
    form = CheckForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["file"]
        data = upload.read(readers.MAX_BYTES + 1)
        result = {"name": upload.name}
        try:
            if len(data) > readers.MAX_BYTES:
                raise readers.SourceError("Plik jest większy niż 10 MB.")
            kind = readers.detect_kind(upload.name, data)
            table = readers.read(upload.name, data)
            if kind == "csv":
                payload, ignored = data, []
            else:
                payload, ignored = table_to_profile_csv(table)
            errors = standard.validate_bytes(payload)
            suggested = mapping.suggest([column for column in table.columns if column not in standard.field_names()])
            result.update({"kind": kind, "records": len(table.rows), "errors": errors, "ignored": ignored,
                           "suggested": len(suggested), "valid": not errors})
        except readers.SourceError as exc:
            result.update({"read_error": str(exc), "valid": False})
    return render(request, "aed_wizard/check.html", {
        "form": form, "result": result, "standard_version": standard.version(), "downloads": list(DOWNLOADS),
    })
