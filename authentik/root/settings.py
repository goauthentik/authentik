"""root settings for authentik"""

import importlib
from collections import OrderedDict
from hashlib import sha512
from pathlib import Path

import orjson
from celery.schedules import crontab
from sentry_sdk import set_tag
from xmlsec import enable_debug_trace

from authentik import __version__
from authentik.lib.config import CONFIG, django_db_config, redis_url
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
    "django_tenants",
    "authentik.tenants",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "django_prometheus",
    "django_countries",
    "pgactivity",
    "pglock",
    "channels",
]
TENANT_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "authentik.admin",
    "authentik.api",
    "authentik.crypto",
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
    "VERSION": __version__,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v([0-9]+(beta)?)",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVERS": [
        {
            "url": "/api/v3/",
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
        "UserTypeEnum": "authentik.core.models.UserTypes",
        "UserVerificationEnum": "authentik.stages.authenticator_webauthn.models.UserVerification",
    },
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    "ENUM_GENERATE_CHOICE_DESCRIPTION": False,
    "PREPROCESSING_HOOKS": [
        "authentik.api.schema.preprocess_schema_exclude_non_api",
    ],
    "POSTPROCESSING_HOOKS": [
        "authentik.api.schema.postprocess_schema_responses",
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
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": CONFIG.get("cache.url") or redis_url(CONFIG.get("redis.db")),
        "TIMEOUT": CONFIG.get_int("cache.timeout", 300),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "authentik_cache",
        "KEY_FUNCTION": "django_tenants.cache.make_key",
        "REVERSE_KEY_FUNCTION": "django_tenants.cache.reverse_key",
    }
}
DJANGO_REDIS_SCAN_ITERSIZE = 1000
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True
SESSION_ENGINE = "authentik.core.sessions"
# Configured via custom SessionMiddleware
# SESSION_COOKIE_SAMESITE = "None"
# SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = timedelta_from_string(
    CONFIG.get("sessions.unauthenticated_age", "days=1")
).total_seconds()
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

MESSAGE_STORAGE = "authentik.root.messages.storage.ChannelsStorage"

MIDDLEWARE = [
    "django_tenants.middleware.default.DefaultTenantMiddleware",
    "authentik.root.middleware.LoggingMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "authentik.root.middleware.ClientIPMiddleware",
    "authentik.stages.user_login.middleware.BoundSessionMiddleware",
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

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [CONFIG.get("channel.url") or redis_url(CONFIG.get("redis.db"))],
            "prefix": "authentik_channels_",
        },
    },
}


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

ORIGINAL_BACKEND = "django_prometheus.db.backends.postgresql"
DATABASES = django_db_config()

DATABASE_ROUTERS = (
    "authentik.tenants.db.FailoverRouter",
    "django_tenants.routers.TenantSyncRouter",
)

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

CELERY = {
    "task_soft_time_limit": 600,
    "worker_max_tasks_per_child": 50,
    "worker_concurrency": CONFIG.get_int("worker.concurrency"),
    "beat_schedule": {
        "clean_expired_models": {
            "task": "authentik.core.tasks.clean_expired_models",
            "schedule": crontab(minute="2-59/5"),
            "options": {"queue": "authentik_scheduled"},
        },
        "user_cleanup": {
            "task": "authentik.core.tasks.clean_temporary_users",
            "schedule": crontab(minute="9-59/5"),
            "options": {"queue": "authentik_scheduled"},
        },
    },
    "beat_scheduler": "authentik.tenants.scheduler:TenantAwarePersistentScheduler",
    "task_create_missing_queues": True,
    "task_default_queue": "authentik",
    "broker_url": CONFIG.get("broker.url") or redis_url(CONFIG.get("redis.db")),
    "result_backend": CONFIG.get("result_backend.url") or redis_url(CONFIG.get("redis.db")),
    "broker_transport_options": CONFIG.get_dict_from_b64_json(
        "broker.transport_options", {"retry_policy": {"timeout": 5.0}}
    ),
    "result_backend_transport_options": CONFIG.get_dict_from_b64_json(
        "result_backend.transport_options", {"retry_policy": {"timeout": 5.0}}
    ),
    "redis_retry_on_timeout": True,
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

TEST = False
TEST_RUNNER = "authentik.root.test_runner.PytestTestRunner"

structlog_configure()
LOGGING = get_logger_config()


_DISALLOWED_ITEMS = [
    "SHARED_APPS",
    "TENANT_APPS",
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "AUTHENTICATION_BACKENDS",
    "CELERY",
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


def _update_settings(app_path: str):
    try:
        settings_module = importlib.import_module(app_path)
        CONFIG.log("debug", "Loaded app settings", path=app_path)
        SHARED_APPS.extend(getattr(settings_module, "SHARED_APPS", []))
        TENANT_APPS.extend(getattr(settings_module, "TENANT_APPS", []))
        MIDDLEWARE.extend(getattr(settings_module, "MIDDLEWARE", []))
        AUTHENTICATION_BACKENDS.extend(getattr(settings_module, "AUTHENTICATION_BACKENDS", []))
        SPECTACULAR_SETTINGS.update(getattr(settings_module, "SPECTACULAR_SETTINGS", {}))
        REST_FRAMEWORK.update(getattr(settings_module, "REST_FRAMEWORK", {}))
        CELERY["beat_schedule"].update(getattr(settings_module, "CELERY_BEAT_SCHEDULE", {}))
        for _attr in dir(settings_module):
            if not _attr.startswith("__") and _attr not in _DISALLOWED_ITEMS:
                globals()[_attr] = getattr(settings_module, _attr)
    except ImportError:
        pass


if DEBUG:
    CELERY["task_always_eager"] = True
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
        "rest_framework.renderers.BrowsableAPIRenderer"
    )
    SHARED_APPS.insert(SHARED_APPS.index("django.contrib.staticfiles"), "daphne")
    enable_debug_trace(True)

TENANT_APPS.append("authentik.core")

CONFIG.log("info", "Booting authentik", version=__version__)

# Attempt to load enterprise app, if available
try:
    importlib.import_module("authentik.enterprise.apps")
    CONFIG.log("info", "Enabled authentik enterprise")
    TENANT_APPS.append("authentik.enterprise")
    _update_settings("authentik.enterprise.settings")
except ImportError:
    pass

# Import events after other apps since it relies on tasks and other things from all apps
# being imported for @prefill_task
TENANT_APPS.append("authentik.events")


# Load subapps's settings
for _app in set(SHARED_APPS + TENANT_APPS):
    if not _app.startswith("authentik"):
        continue
    _update_settings(f"{_app}.settings")
_update_settings("data.user_settings")

SHARED_APPS = list(OrderedDict.fromkeys(SHARED_APPS + TENANT_APPS))
INSTALLED_APPS = list(OrderedDict.fromkeys(SHARED_APPS + TENANT_APPS))
