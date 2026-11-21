from mcod.settings.base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa: F405
INTERNAL_IPS = (
    "127.0.0.1",
    "localhost",
    "172.18.18.100",
)  # needed to use debug processor in django templates


if EMAIL_HOST:  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
else:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = "/tmp/app-messages"

NO_REPLY_EMAIL = "no-reply@mcod.local"

ELASTICSEARCH_DSL_INDEX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
}

ELASTICSEARCH_HISTORIES_IDX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
}

CELERY_TASK_ALWAYS_EAGER = False

FIXTURE_DIRS = [
    str(ROOT_DIR("test-data/fixtures")),
]

MEDIA_ROOT = str(ROOT_DIR("media"))
ACADEMY_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "academy"))
IMAGES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "images"))
LABORATORY_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "lab_reports"))
MEETINGS_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "meetings"))
NEWSLETTER_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "newsletter"))
RESOURCES_FILES_TO_REMOVE_ROOT = str(
    ROOT_DIR.path(MEDIA_ROOT, "to_be_removed", "resources")
)
RESOURCES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "resources"))
SHOWCASES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "showcases"))

SESSION_COOKIE_NAME = "local_sessionid"
SESSION_COOKIE_DOMAIN = "mcod.local"
SESSION_COOKIE_SECURE = False
API_TOKEN_COOKIE_NAME = "local_apiauthtoken"


LOGGING["loggers"]["django.db.backends"]["level"] = "ERROR"
LOGGING["loggers"]["django.db.backends"]["handlers"] = ["console"]
LOGGING["loggers"]["django.request"]["level"] = "DEBUG"
LOGGING["loggers"]["django.request"]["handlers"] = ["console"]
LOGGING["loggers"]["django.server"]["level"] = "DEBUG"
LOGGING["loggers"]["django.server"]["handlers"] = ["console"]
LOGGING["loggers"]["signals"]["level"] = "DEBUG"
LOGGING["loggers"]["signals"]["handlers"] = ["signals-console-handler"]
LOGGING["loggers"]["celery.app.trace"]["level"] = "WARNING"
LOGGING["loggers"]["celery.app.trace"]["handlers"] = ["console"]
LOGGING["loggers"]["mcod"]["handlers"] = ["console"]
LOGGING["loggers"]["resource_file_processing"]["handlers"] = ["console"]
LOGGING['loggers']['mcod-api']['level'] = 'DEBUG'

COMPONENT = env("COMPONENT", default="admin")
ENVIRONMENT = "local"

AXES_ENABLED=False

# Local jury runtime, 2026-11-21: no production telemetry.
UNLEASH_URL = "http://flags/api"
MATOMO_URL = ""
MATOMO_SITE_ID = ""
ENABLE_SENTRY = False

# Local AED modules, 2026-11-21.
INSTALLED_APPS += ["mcod.aed_aggregate"]  # noqa: F405

# AED provider wizard (APP-43, 2026-11-21): reference profile from aed-standard/.
INSTALLED_APPS += ["mcod.aed_wizard"]  # noqa: F405
AED_STANDARD_DIR = env("AED_STANDARD_DIR", default=str(ROOT_DIR.path("..", "aed-standard")))  # noqa: F405
SUIT_CONFIG["MENU"][0]["models"].insert(0, {"label": "Dodaj dane AED", "url": "/aed/kreator/", "icon": "icon-heart"})  # noqa: F405

# AED incident reports, QR codes and device registry (APP-45, 2026-11-21).
INSTALLED_APPS += ["mcod.aed_reports"]  # noqa: F405
SUIT_CONFIG["MENU"][0]["models"] += [  # noqa: F405
    {"model": "aed_reports.aedincidentreport", "label": "Zgłoszenia AED", "icon": "icon-bullhorn"},
    {"model": "aed_reports.aeddevice", "label": "Urządzenia AED", "icon": "icon-map-marker"},
]
