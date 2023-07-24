"""root settings for authentik"""

import importlib
import logging
import os
from hashlib import sha512
from pathlib import Path
from urllib.parse import quote_plus

import structlog
from celery.schedules import crontab
from sentry_sdk import set_tag

from authentik import ENV_GIT_HASH_KEY, __version__
from authentik.lib.config import CONFIG
from authentik.lib.logging import add_process_id
from authentik.lib.sentry import sentry_init
from authentik.lib.utils.reflection import get_env
from authentik.stages.password import BACKEND_APP_PASSWORD, BACKEND_INBUILT, BACKEND_LDAP

LOGGER = structlog.get_logger()

BASE_DIR = Path(__file__).absolute().parent.parent.parent
STATICFILES_DIRS = [BASE_DIR / Path("web")]
MEDIA_ROOT = BASE_DIR / Path("media")

DEBUG = CONFIG.get_bool("debug")
SECRET_KEY = CONFIG.get("secret_key")

INTERNAL_IPS = ["127.0.0.1"]
ALLOWED_HOSTS = ["*"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
LOGIN_URL = "authentik_flows:default-authentication"

# Custom user model
AUTH_USER_MODEL = "authentik_core.User"

CSRF_COOKIE_NAME = "authentik_csrf"
CSRF_HEADER_NAME = "HTTP_X_AUTHENTIK_CSRF"
LANGUAGE_COOKIE_NAME = "authentik_language"
SESSION_COOKIE_NAME = "authentik_session"
SESSION_COOKIE_DOMAIN = CONFIG.get("cookie_domain", None)

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    BACKEND_INBUILT,
    BACKEND_APP_PASSWORD,
    BACKEND_LDAP,
    "guardian.backends.ObjectPermissionBackend",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Application definition
INSTALLED_APPS = [
    "daphne",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "authentik.admin",
    "authentik.api",
    "authentik.crypto",
    "authentik.events",
    "authentik.flows",
    "authentik.lib",
    "authentik.outposts",
    "authentik.policies.dummy",
    "authentik.policies.event_matcher",
    "authentik.policies.expiry",
    "authentik.policies.expression",
    "authentik.policies.password",
    "authentik.policies.reputation",
    "authentik.policies",
    "authentik.providers.ldap",
    "authentik.providers.oauth2",
    "authentik.providers.proxy",
    "authentik.providers.radius",
    "authentik.providers.saml",
    "authentik.providers.scim",
    "authentik.recovery",
    "authentik.sources.ldap",
    "authentik.sources.oauth",
    "authentik.sources.plex",
    "authentik.sources.saml",
    "authentik.stages.authenticator_duo",
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
    "authentik.stages.user_delete",
    "authentik.stages.user_login",
    "authentik.stages.user_logout",
    "authentik.stages.user_write",
    "authentik.tenants",
    "authentik.blueprints",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "guardian",
    "django_prometheus",
    "channels",
]

GUARDIAN_MONKEY_PATCH = False

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
        "EventActions": "authentik.events.models.EventAction",
        "ChallengeChoices": "authentik.flows.challenge.ChallengeTypes",
        "FlowDesignationEnum": "authentik.flows.models.FlowDesignation",
        "PolicyEngineMode": "authentik.policies.models.PolicyEngineMode",
        "ProxyMode": "authentik.providers.proxy.models.ProxyMode",
        "PromptTypeEnum": "authentik.stages.prompt.models.FieldTypes",
        "LDAPAPIAccessMode": "authentik.providers.ldap.models.APIAccessMode",
        "UserVerificationEnum": "authentik.stages.authenticator_webauthn.models.UserVerification",
        "UserTypeEnum": "authentik.core.models.UserTypes",
    },
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    "POSTPROCESSING_HOOKS": [
        "authentik.api.schema.postprocess_schema_responses",
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "authentik.api.pagination.Pagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework_guardian.filters.ObjectPermissionsFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.DjangoObjectPermissions",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "authentik.api.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "anon": CONFIG.get("throttle.default"),
    },
}

_redis_protocol_prefix = "redis://"
_redis_celery_tls_requirements = ""
if CONFIG.get_bool("redis.tls", False):
    _redis_protocol_prefix = "rediss://"
    _redis_celery_tls_requirements = f"?ssl_cert_reqs={CONFIG.get('redis.tls_reqs')}"
_redis_url = (
    f"{_redis_protocol_prefix}:"
    f"{quote_plus(CONFIG.get('redis.password'))}@{quote_plus(CONFIG.get('redis.host'))}:"
    f"{int(CONFIG.get('redis.port'))}"
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{_redis_url}/{CONFIG.get('redis.db')}",
        "TIMEOUT": int(CONFIG.get("redis.cache_timeout", 300)),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "authentik_cache",
    }
}
DJANGO_REDIS_SCAN_ITERSIZE = 1000
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"
SESSION_CACHE_ALIAS = "default"
# Configured via custom SessionMiddleware
# SESSION_COOKIE_SAMESITE = "None"
# SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

MESSAGE_STORAGE = "authentik.root.messages.storage.ChannelsStorage"

MIDDLEWARE = [
    "authentik.root.middleware.LoggingMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "authentik.root.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "authentik.core.middleware.RequestIDMiddleware",
    "authentik.tenants.middleware.TenantMiddleware",
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
                "authentik.tenants.utils.context_processor",
            ],
        },
    },
]

ASGI_APPLICATION = "authentik.root.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [f"{_redis_url}/{CONFIG.get('redis.db')}"],
            "prefix": "authentik_channels",
        },
    },
}


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "authentik.root.db",
        "HOST": CONFIG.get("postgresql.host"),
        "NAME": CONFIG.get("postgresql.name"),
        "USER": CONFIG.get("postgresql.user"),
        "PASSWORD": CONFIG.get("postgresql.password"),
        "PORT": int(CONFIG.get("postgresql.port")),
        "SSLMODE": CONFIG.get("postgresql.sslmode"),
        "SSLROOTCERT": CONFIG.get("postgresql.sslrootcert"),
        "SSLCERT": CONFIG.get("postgresql.sslcert"),
        "SSLKEY": CONFIG.get("postgresql.sslkey"),
    }
}

if CONFIG.get_bool("postgresql.use_pgbouncer", False):
    # https://docs.djangoproject.com/en/4.0/ref/databases/#transaction-pooling-server-side-cursors
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
    # https://docs.djangoproject.com/en/4.0/ref/databases/#persistent-connections
    DATABASES["default"]["CONN_MAX_AGE"] = None  # persistent

# Email
# These values should never actually be used, emails are only sent from email stages, which
# loads the config directly from CONFIG
# See authentik/stages/email/models.py, line 105
EMAIL_HOST = CONFIG.get("email.host")
EMAIL_PORT = int(CONFIG.get("email.port"))
EMAIL_HOST_USER = CONFIG.get("email.username")
EMAIL_HOST_PASSWORD = CONFIG.get("email.password")
EMAIL_USE_TLS = CONFIG.get_bool("email.use_tls", False)
EMAIL_USE_SSL = CONFIG.get_bool("email.use_ssl", False)
EMAIL_TIMEOUT = int(CONFIG.get("email.timeout"))
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
    "worker_concurrency": 2,
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
    "task_create_missing_queues": True,
    "task_default_queue": "authentik",
    "broker_url": f"{_redis_url}/{CONFIG.get('redis.db')}{_redis_celery_tls_requirements}",
    "result_backend": f"{_redis_url}/{CONFIG.get('redis.db')}{_redis_celery_tls_requirements}",
}

# Sentry integration
env = get_env()
_ERROR_REPORTING = CONFIG.get_bool("error_reporting.enabled", False)
if _ERROR_REPORTING:
    sentry_env = CONFIG.get("error_reporting.environment", "customer")
    sentry_init()
    set_tag("authentik.uuid", sha512(str(SECRET_KEY).encode("ascii")).hexdigest()[:16])


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

TEST = False
TEST_RUNNER = "authentik.root.test_runner.PytestTestRunner"
# We can't check TEST here as its set later by the test runner
LOG_LEVEL = CONFIG.get("log_level").upper() if "TF_BUILD" not in os.environ else "DEBUG"
# We could add a custom level to stdlib logging and structlog, but it's not easy or clean
# https://stackoverflow.com/questions/54505487/custom-log-level-not-working-with-structlog
# Additionally, the entire code uses debug as highest level so that would have to be re-written too
if LOG_LEVEL == "TRACE":
    LOG_LEVEL = "DEBUG"

structlog.configure_once(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.contextvars.merge_contextvars,
        add_process_id,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.dict_tracebacks,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, LOG_LEVEL, logging.WARNING)
    ),
    cache_logger_on_first_use=True,
)

LOG_PRE_CHAIN = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(),
    structlog.processors.StackInfoRenderer(),
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(sort_keys=True),
            "foreign_pre_chain": LOG_PRE_CHAIN,
        },
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=DEBUG),
            "foreign_pre_chain": LOG_PRE_CHAIN,
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console" if DEBUG else "json",
        },
    },
    "loggers": {},
}

_LOGGING_HANDLER_MAP = {
    "": LOG_LEVEL,
    "authentik": LOG_LEVEL,
    "django": "WARNING",
    "django.request": "ERROR",
    "celery": "WARNING",
    "selenium": "WARNING",
    "docker": "WARNING",
    "urllib3": "WARNING",
    "websockets": "WARNING",
    "daphne": "WARNING",
    "kubernetes": "INFO",
    "asyncio": "WARNING",
    "redis": "WARNING",
    "silk": "INFO",
    "fsevents": "WARNING",
}
for handler_name, level in _LOGGING_HANDLER_MAP.items():
    LOGGING["loggers"][handler_name] = {
        "handlers": ["console"],
        "level": level,
        "propagate": False,
    }


_DISALLOWED_ITEMS = [
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "AUTHENTICATION_BACKENDS",
    "CELERY",
]


def _update_settings(app_path: str):
    try:
        settings_module = importlib.import_module(app_path)
        CONFIG.log("debug", "Loaded app settings", path=app_path)
        INSTALLED_APPS.extend(getattr(settings_module, "INSTALLED_APPS", []))
        MIDDLEWARE.extend(getattr(settings_module, "MIDDLEWARE", []))
        AUTHENTICATION_BACKENDS.extend(getattr(settings_module, "AUTHENTICATION_BACKENDS", []))
        CELERY["beat_schedule"].update(getattr(settings_module, "CELERY_BEAT_SCHEDULE", {}))
        for _attr in dir(settings_module):
            if not _attr.startswith("__") and _attr not in _DISALLOWED_ITEMS:
                globals()[_attr] = getattr(settings_module, _attr)
    except ImportError:
        pass


# Load subapps's settings
for _app in INSTALLED_APPS:
    if not _app.startswith("authentik"):
        continue
    _update_settings(f"{_app}.settings")
_update_settings("data.user_settings")

if DEBUG:
    CELERY["task_always_eager"] = True
    os.environ[ENV_GIT_HASH_KEY] = "dev"
    INSTALLED_APPS.append("silk")
    SILKY_PYTHON_PROFILER = True
    MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE

INSTALLED_APPS.append("authentik.core")

CONFIG.log("info", "Booting authentik", version=__version__)

# Attempt to load enterprise app, if available
try:
    importlib.import_module("authentik.enterprise.apps")
    CONFIG.log("info", "Enabled authentik enterprise")
    INSTALLED_APPS.append("authentik.enterprise")
    _update_settings("authentik.enterprise.settings")
except ImportError:
    pass
