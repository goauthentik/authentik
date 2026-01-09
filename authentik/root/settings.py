"""root settings for authentik"""

import importlib
from collections import OrderedDict
from hashlib import sha512
from pathlib import Path

import orjson
from django.http import response as http_response
from sentry_sdk import set_tag
from xmlsec import enable_debug_trace

from authentik import authentik_version
from authentik.lib.config import CONFIG, django_db_config
from authentik.lib.logging import get_logger_config, structlog_configure
from authentik.lib.sentry import sentry_init
from authentik.lib.utils.reflection import get_env
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.password import BACKEND_APP_PASSWORD, BACKEND_INBUILT, BACKEND_LDAP

BASE_DIR = Path(__file__).absolute().parent.parent.parent

DEBUG = CONFIG.get_bool("debug")
SECRET_KEY = CONFIG.get("secret_key")

INTERNAL_IPS = ["127.0.0.1"]
ALLOWED_HOSTS = ["*"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
LOGIN_URL = "authentik_flows:default-authentication"

# Custom user model
AUTH_USER_MODEL = "authentik_core.User"

CSRF_COOKIE_PATH = LANGUAGE_COOKIE_PATH = SESSION_COOKIE_PATH = CONFIG.get("web.path", "/")

CSRF_COOKIE_NAME = "authentik_csrf"
CSRF_HEADER_NAME = "HTTP_X_AUTHENTIK_CSRF"
LANGUAGE_COOKIE_NAME = "authentik_language"
SESSION_COOKIE_NAME = "authentik_session"
SESSION_COOKIE_DOMAIN = CONFIG.get("cookie_domain", None)
APPEND_SLASH = False

AUTHENTICATION_BACKENDS = [
    BACKEND_INBUILT,
    BACKEND_APP_PASSWORD,
    BACKEND_LDAP,
    "guardian.backends.ObjectPermissionBackend",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Application definition
SHARED_APPS = [
    "authentik.commands",
    "django_tenants",
    "authentik.tenants",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "psqlextra",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "django_prometheus",
    "django_countries",
    "pgactivity",
    "pglock",
    "channels",
    "django_channels_postgres",
    "django_dramatiq_postgres",
    "authentik.tasks",
]
TENANT_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "pgtrigger",
    "django_postgres_cache",
    "authentik.admin",
    "authentik.api",
    "authentik.core",
    "authentik.crypto",
    "authentik.enterprise",
    "authentik.events",
    "authentik.flows",
    "authentik.outposts",
    "authentik.policies.dummy",
    "authentik.policies.event_matcher",
    "authentik.policies.expiry",
    "authentik.policies.expression",
    "authentik.policies.geoip",
    "authentik.policies.password",
    "authentik.policies.reputation",
    "authentik.policies",
    "authentik.providers.ldap",
    "authentik.providers.oauth2",
    "authentik.providers.proxy",
    "authentik.providers.rac",
    "authentik.providers.radius",
    "authentik.providers.saml",
    "authentik.providers.scim",
    "authentik.rbac",
    "authentik.recovery",
    "authentik.sources.kerberos",
    "authentik.sources.ldap",
    "authentik.sources.oauth",
    "authentik.sources.plex",
    "authentik.sources.saml",
    "authentik.sources.scim",
    "authentik.sources.telegram",
    "authentik.stages.authenticator",
    "authentik.stages.authenticator_duo",
    "authentik.stages.authenticator_email",
    "authentik.stages.authenticator_sms",
    "authentik.stages.authenticator_static",
    "authentik.stages.authenticator_totp",
    "authentik.stages.authenticator_validate",
    "authentik.stages.authenticator_webauthn",
    "authentik.stages.captcha",
    "authentik.stages.consent",
    "authentik.stages.deny",
    "authentik.stages.dummy",
    "authentik.stages.email",
    "authentik.stages.identification",
    "authentik.stages.invitation",
    "authentik.stages.password",
    "authentik.stages.prompt",
    "authentik.stages.redirect",
    "authentik.stages.user_delete",
    "authentik.stages.user_login",
    "authentik.stages.user_logout",
    "authentik.stages.user_write",
    "authentik.tasks.schedules",
    "authentik.brands",
    "authentik.blueprints",
    "guardian",
]

TENANT_MODEL = "authentik_tenants.Tenant"
TENANT_DOMAIN_MODEL = "authentik_tenants.Domain"

TENANT_CREATION_FAKES_MIGRATIONS = True
TENANT_BASE_SCHEMA = "template"
PUBLIC_SCHEMA_NAME = CONFIG.get("postgresql.default_schema")

GUARDIAN_MONKEY_PATCH_USER = False

SPECTACULAR_SETTINGS = {
    "TITLE": "authentik",
    "DESCRIPTION": "Making authentication simple.",
    "VERSION": authentik_version(),
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v([0-9]+(beta)?)",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVERS": [
        {
            "url": "/api/v3",
        },
    ],
    "CONTACT": {
        "email": "hello@goauthentik.io",
    },
    "AUTHENTICATION_WHITELIST": ["authentik.api.authentication.TokenAuthentication"],
    "LICENSE": {
        "name": "MIT",
        "url": "https://github.com/goauthentik/authentik/blob/main/LICENSE",
    },
    "ENUM_NAME_OVERRIDES": {
        "CountryCodeEnum": "django_countries.countries",
        "DeviceClassesEnum": "authentik.stages.authenticator_validate.models.DeviceClasses",
        "EventActions": "authentik.events.models.EventAction",
        "FlowDesignationEnum": "authentik.flows.models.FlowDesignation",
        "FlowLayoutEnum": "authentik.flows.models.FlowLayout",
        "LDAPAPIAccessMode": "authentik.providers.ldap.models.APIAccessMode",
        "OutgoingSyncDeleteAction": "authentik.lib.sync.outgoing.models.OutgoingSyncDeleteAction",
        "PolicyEngineMode": "authentik.policies.models.PolicyEngineMode",
        "PromptTypeEnum": "authentik.stages.prompt.models.FieldTypes",
        "ProxyMode": "authentik.providers.proxy.models.ProxyMode",
        "TaskAggregatedStatusEnum": "authentik.tasks.models.TaskStatus",
        "SAMLNameIDPolicyEnum": "authentik.sources.saml.models.SAMLNameIDPolicy",
        "SAMLBindingsEnum": "authentik.providers.saml.models.SAMLBindings",
        "UserTypeEnum": "authentik.core.models.UserTypes",
        "UserVerificationEnum": "authentik.stages.authenticator_webauthn.models.UserVerification",
        "SCIMAuthenticationModeEnum": "authentik.providers.scim.models.SCIMAuthenticationMode",
        "PKCEMethodEnum": "authentik.sources.oauth.models.PKCEMethod",
    },
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    "ENUM_GENERATE_CHOICE_DESCRIPTION": False,
    "PREPROCESSING_HOOKS": [
        "authentik.api.schema.preprocess_schema_exclude_non_api",
    ],
    "POSTPROCESSING_HOOKS": [
        "authentik.api.schema.postprocess_schema_register",
        "authentik.api.schema.postprocess_schema_responses",
        "authentik.api.schema.postprocess_schema_query_params",
        "authentik.api.schema.postprocess_schema_remove_unused",
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "authentik.api.pagination.Pagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": [
        "authentik.rbac.filters.ObjectFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("authentik.rbac.permissions.ObjectPermissions",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "authentik.api.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": [
        "drf_orjson_renderer.renderers.ORJSONRenderer",
    ],
    "ORJSON_RENDERER_OPTIONS": [
        orjson.OPT_NON_STR_KEYS,
        orjson.OPT_UTC_Z,
    ],
    "DEFAULT_PARSER_CLASSES": [
        "drf_orjson_renderer.parsers.ORJSONParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "anon": CONFIG.get("throttle.default"),
    },
}


CACHES = {
    "default": {
        "BACKEND": "django_postgres_cache.backend.DatabaseCache",
        "KEY_FUNCTION": "django_tenants.cache.make_key",
        "REVERSE_KEY_FUNCTION": "django_tenants.cache.reverse_key",
    }
}
SESSION_ENGINE = "authentik.core.sessions"
# Configured via custom SessionMiddleware
# SESSION_COOKIE_SAMESITE = "None"
# SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = timedelta_from_string(
    CONFIG.get("sessions.unauthenticated_age", "days=1")
).total_seconds()
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

MESSAGE_STORAGE = "authentik.root.ws.storage.ChannelsStorage"

MIDDLEWARE_FIRST = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
]
MIDDLEWARE = [
    "django_tenants.middleware.default.DefaultTenantMiddleware",
    "authentik.root.middleware.LoggingMiddleware",
    "authentik.root.middleware.ClientIPMiddleware",
    "authentik.stages.user_login.middleware.BoundSessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "authentik.core.middleware.AuthenticationMiddleware",
    "authentik.core.middleware.RequestIDMiddleware",
    "authentik.brands.middleware.BrandMiddleware",
    "authentik.events.middleware.AuditMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "authentik.root.middleware.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authentik.core.middleware.ImpersonateMiddleware",
    "authentik.rbac.middleware.InitialPermissionsMiddleware",
]
MIDDLEWARE_LAST = [
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "authentik.root.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [CONFIG.get("email.template_dir")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "authentik.brands.utils.context_processor",
            ],
        },
    },
]

ASGI_APPLICATION = "authentik.root.asgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# Custom overrides for database backends
# The tree looks like this:
# psqlextra backend
#   -> authentik custom backend
#     -> django_tenants backend
#       -> django_prometheus backend
#         -> django built-in backend
ORIGINAL_BACKEND = "django_prometheus.db.backends.postgresql"
POSTGRES_EXTRA_DB_BACKEND_BASE = "authentik.root.db"
DATABASES = django_db_config()

DATABASE_ROUTERS = (
    "authentik.tenants.db.FailoverRouter",
    "django_tenants.routers.TenantSyncRouter",
)

# We don't use HStore
POSTGRES_EXTRA_AUTO_EXTENSION_SET_UP = False

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "django_channels_postgres.layer.PostgresChannelLayer",
    },
}

# Email
# These values should never actually be used, emails are only sent from email stages, which
# loads the config directly from CONFIG
# See authentik/stages/email/models.py, line 105
EMAIL_HOST = CONFIG.get("email.host")
EMAIL_PORT = CONFIG.get_int("email.port")
EMAIL_HOST_USER = CONFIG.get("email.username")
EMAIL_HOST_PASSWORD = CONFIG.get("email.password")
EMAIL_USE_TLS = CONFIG.get_bool("email.use_tls", False)
EMAIL_USE_SSL = CONFIG.get_bool("email.use_ssl", False)
EMAIL_TIMEOUT = CONFIG.get_int("email.timeout")
DEFAULT_FROM_EMAIL = CONFIG.get("email.from")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_SUBJECT_PREFIX = "[authentik] "

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = ["./locale"]


# Tests

TEST = False
TEST_RUNNER = "authentik.root.test_runner.PytestTestRunner"


# Dramatiq

DRAMATIQ = {
    "broker_class": "authentik.tasks.broker.Broker",
    "channel_prefix": "authentik",
    "task_model": "authentik.tasks.models.Task",
    "task_purge_interval": timedelta_from_string(
        CONFIG.get("worker.task_purge_interval")
    ).total_seconds(),
    "task_expiration": timedelta_from_string(CONFIG.get("worker.task_expiration")).total_seconds(),
    "autodiscovery": {
        "enabled": True,
        "setup_module": "authentik.tasks.setup",
        "apps_prefix": "authentik",
    },
    "worker": {
        "processes": CONFIG.get_int("worker.processes", 2),
        "threads": CONFIG.get_int("worker.threads", 1),
        "consumer_listen_timeout": timedelta_from_string(
            CONFIG.get("worker.consumer_listen_timeout")
        ).total_seconds(),
        "watch_folder": BASE_DIR / "authentik",
    },
    "scheduler_class": "authentik.tasks.schedules.scheduler.Scheduler",
    "schedule_model": "authentik.tasks.schedules.models.Schedule",
    "scheduler_interval": timedelta_from_string(
        CONFIG.get("worker.scheduler_interval")
    ).total_seconds(),
    "middlewares": (
        ("django_dramatiq_postgres.middleware.FullyQualifiedActorName", {}),
        ("django_dramatiq_postgres.middleware.DbConnectionMiddleware", {}),
        ("django_dramatiq_postgres.middleware.TaskStateBeforeMiddleware", {}),
        ("dramatiq.middleware.age_limit.AgeLimit", {}),
        (
            "dramatiq.middleware.time_limit.TimeLimit",
            {
                "time_limit": timedelta_from_string(
                    CONFIG.get("worker.task_default_time_limit")
                ).total_seconds()
                * 1000
            },
        ),
        ("dramatiq.middleware.shutdown.ShutdownNotifications", {}),
        ("dramatiq.middleware.callbacks.Callbacks", {}),
        ("dramatiq.middleware.pipelines.Pipelines", {}),
        (
            "dramatiq.middleware.retries.Retries",
            {
                "max_retries": CONFIG.get_int("worker.task_max_retries") if not TEST else 0,
                "max_backoff": 60 * 60 * 1000,  # 1 hour
            },
        ),
        ("dramatiq.results.middleware.Results", {"store_results": True}),
        ("authentik.tasks.middleware.StartupSignalsMiddleware", {}),
        ("authentik.tasks.middleware.CurrentTask", {}),
        ("authentik.tasks.middleware.TenantMiddleware", {}),
        ("authentik.tasks.middleware.ModelDataMiddleware", {}),
        ("authentik.tasks.middleware.TaskLogMiddleware", {}),
        ("authentik.tasks.middleware.LoggingMiddleware", {}),
        ("authentik.tasks.middleware.DescriptionMiddleware", {}),
        ("authentik.tasks.middleware.WorkerHealthcheckMiddleware", {}),
        ("authentik.tasks.middleware.WorkerStatusMiddleware", {}),
        (
            "authentik.tasks.middleware.MetricsMiddleware",
            {
                "prefix": "authentik",
            },
        ),
        ("django_dramatiq_postgres.middleware.TaskStateAfterMiddleware", {}),
    ),
    "test": TEST,
}


# Sentry integration

env = get_env()
_ERROR_REPORTING = CONFIG.get_bool("error_reporting.enabled", False)
if _ERROR_REPORTING:
    sentry_env = CONFIG.get("error_reporting.environment", "customer")
    sentry_init(spotlight=DEBUG)
    set_tag("authentik.uuid", sha512(str(SECRET_KEY).encode("ascii")).hexdigest()[:16])


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATICFILES_DIRS = [BASE_DIR / Path("web")]
STATIC_URL = CONFIG.get("web.path", "/") + "static/"

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Django 5.2.8 and CVE-2025-64458 added a strong enforcement of 2048 characters
# as the maximum for a URL to redirect to, mostly for running on windows.
# However our URLs can easily exceed that with OAuth/SAML Query parameters or hash values
# 8192 should cover most cases..
http_response.MAX_URL_LENGTH = http_response.MAX_URL_LENGTH * 4


# Media files
if CONFIG.get("storage.media.backend", "file") == "s3":
    STORAGES["default"] = {
        "BACKEND": "authentik.root.storages.S3Storage",
        "OPTIONS": {
            # How to talk to S3
            "session_profile": CONFIG.get("storage.media.s3.session_profile", None),
            "access_key": CONFIG.get("storage.media.s3.access_key", None),
            "secret_key": CONFIG.get("storage.media.s3.secret_key", None),
            "security_token": CONFIG.get("storage.media.s3.security_token", None),
            "region_name": CONFIG.get("storage.media.s3.region", None),
            "use_ssl": CONFIG.get_bool("storage.media.s3.use_ssl", True),
            "endpoint_url": CONFIG.get("storage.media.s3.endpoint", None),
            "bucket_name": CONFIG.get("storage.media.s3.bucket_name"),
            "default_acl": "private",
            "querystring_auth": True,
            "signature_version": "s3v4",
            "file_overwrite": False,
            "location": "media",
            "url_protocol": (
                "https:" if CONFIG.get("storage.media.s3.secure_urls", True) else "http:"
            ),
            "custom_domain": CONFIG.get("storage.media.s3.custom_domain", None),
        },
    }
# Fallback on file storage backend
else:
    STORAGES["default"] = {
        "BACKEND": "authentik.root.storages.FileStorage",
        "OPTIONS": {
            "location": Path(CONFIG.get("storage.media.file.path")),
            "base_url": CONFIG.get("web.path", "/") + "media/",
        },
    }
    # Compatibility for apps not supporting top-level STORAGES
    # such as django-tenants
    MEDIA_ROOT = STORAGES["default"]["OPTIONS"]["location"]
    MEDIA_URL = STORAGES["default"]["OPTIONS"]["base_url"]

structlog_configure()
LOGGING = get_logger_config()


_DISALLOWED_ITEMS = [
    "SHARED_APPS",
    "TENANT_APPS",
    "INSTALLED_APPS",
    "MIDDLEWARE_FIRST",
    "MIDDLEWARE",
    "MIDDLEWARE_LAST",
    "AUTHENTICATION_BACKENDS",
    "SPECTACULAR_SETTINGS",
    "REST_FRAMEWORK",
]

SILENCED_SYSTEM_CHECKS = [
    # We use our own subclass of django.middleware.csrf.CsrfViewMiddleware
    "security.W003",
    # We don't set SESSION_COOKIE_SECURE since we use a custom SessionMiddleware subclass
    "security.W010",
    # HSTS: This is configured in reverse proxies/the go proxy, not in django
    "security.W004",
    # https redirect: This is configured in reverse proxies/the go proxy, not in django
    "security.W008",
]


def subtract_list(a: list, b: list) -> list:
    return [item for item in a if item not in b]


def _filter_and_update(apps: list[str]) -> None:
    for _app in set(apps):
        if not _app.startswith("authentik"):
            continue
        _update_settings(f"{_app}.settings")


def _update_settings(app_path: str) -> None:
    try:
        settings_module = importlib.import_module(app_path)
        CONFIG.log("debug", "Loaded app settings", path=app_path)

        new_shared_apps = subtract_list(getattr(settings_module, "SHARED_APPS", []), SHARED_APPS)
        new_tenant_apps = subtract_list(getattr(settings_module, "TENANT_APPS", []), TENANT_APPS)
        SHARED_APPS.extend(new_shared_apps)
        TENANT_APPS.extend(new_tenant_apps)
        _filter_and_update(new_shared_apps + new_tenant_apps)

        MIDDLEWARE_FIRST.extend(getattr(settings_module, "MIDDLEWARE_FIRST", []))
        MIDDLEWARE.extend(getattr(settings_module, "MIDDLEWARE", []))

        AUTHENTICATION_BACKENDS.extend(getattr(settings_module, "AUTHENTICATION_BACKENDS", []))
        SPECTACULAR_SETTINGS.update(getattr(settings_module, "SPECTACULAR_SETTINGS", {}))
        REST_FRAMEWORK.update(getattr(settings_module, "REST_FRAMEWORK", {}))

        for _attr in dir(settings_module):
            if not _attr.startswith("__") and _attr not in _DISALLOWED_ITEMS:
                globals()[_attr] = getattr(settings_module, _attr)
    except ImportError:
        pass


if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
        "rest_framework.renderers.BrowsableAPIRenderer"
    )
    SHARED_APPS.insert(SHARED_APPS.index("django.contrib.staticfiles"), "daphne")
    enable_debug_trace(True)


CONFIG.log("info", "Booting authentik", version=authentik_version())

# Load subapps's settings
_filter_and_update(SHARED_APPS + TENANT_APPS)
_update_settings("data.user_settings")

MIDDLEWARE = list(OrderedDict.fromkeys(MIDDLEWARE_FIRST + MIDDLEWARE + MIDDLEWARE_LAST))
SHARED_APPS = list(OrderedDict.fromkeys(SHARED_APPS + TENANT_APPS))
INSTALLED_APPS = list(OrderedDict.fromkeys(SHARED_APPS + TENANT_APPS))
