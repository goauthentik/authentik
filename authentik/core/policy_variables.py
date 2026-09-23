"""Policy variables provided by core"""

from django.utils.translation import gettext_lazy as _

from authentik.core.models import Application, UserTypes
from authentik.policies.conditional.registry import (
    FACT_HTTP_REQUEST,
    FACT_USER,
    ParamKind,
    registry,
)
from authentik.policies.conditional.types import MISSING, T, dig
from authentik.policies.types import PolicyRequest

FACT_APPLICATION = "application"

registry.fact(
    FACT_APPLICATION,
    _("Application"),
    _("The application the user is accessing."),
)
registry.target("authentik_core.application", [FACT_HTTP_REQUEST, FACT_APPLICATION])

_USER = [FACT_USER]


@registry.variable("user.username", _("Username"), T.STRING, requires=_USER)
def user_username(request: PolicyRequest):
    return request.user.username


@registry.variable("user.name", _("Name"), T.STRING, requires=_USER)
def user_name(request: PolicyRequest):
    return request.user.name


@registry.variable("user.email", _("Email"), T.STRING, requires=_USER)
def user_email(request: PolicyRequest):
    return request.user.email or MISSING


@registry.variable("user.is_active", _("Is active"), T.BOOLEAN, requires=_USER)
def user_is_active(request: PolicyRequest):
    return request.user.is_active


@registry.variable(
    "user.is_authenticated",
    _("Is authenticated"),
    T.BOOLEAN,
    requires=_USER,
    description=_("False when the policy is evaluated for an anonymous user."),
)
def user_is_authenticated(request: PolicyRequest):
    return bool(request.user.pk) and not request.user.is_anonymous


@registry.variable("user.type", _("Type"), T.enum(UserTypes.choices), requires=_USER)
def user_type(request: PolicyRequest):
    return request.user.type


@registry.variable("user.path", _("Path"), T.STRING, requires=_USER)
def user_path(request: PolicyRequest):
    return request.user.path


@registry.variable("user.date_joined", _("Date joined"), T.DATETIME, requires=_USER)
def user_date_joined(request: PolicyRequest):
    return request.user.date_joined


@registry.variable("user.last_login", _("Last login"), T.DATETIME, requires=_USER)
def user_last_login(request: PolicyRequest):
    return request.user.last_login


@registry.variable(
    "user.groups",
    _("Groups"),
    T.list(T.model("authentik_core.group")),
    requires=_USER,
    description=_("Groups the user is a member of, including inherited groups."),
)
def user_groups(request: PolicyRequest):
    if not request.user.pk:
        return []
    return list(request.user.all_groups().values_list("pk", flat=True))


@registry.variable(
    "user.attributes",
    _("Attribute"),
    T.ANY,
    requires=_USER,
    param=ParamKind.PATH,
    description=_("Value of the user's attributes at the given dotted path."),
)
def user_attributes(request: PolicyRequest, path: str):
    return dig(request.user.attributes, path)


def _application(request: PolicyRequest) -> Application | None:
    if isinstance(request.obj, Application):
        return request.obj
    return None


@registry.variable("application.slug", _("Application slug"), T.STRING, requires=[FACT_APPLICATION])
def application_slug(request: PolicyRequest):
    app = _application(request)
    return app.slug if app else MISSING


@registry.variable("application.name", _("Application name"), T.STRING, requires=[FACT_APPLICATION])
def application_name(request: PolicyRequest):
    app = _application(request)
    return app.name if app else MISSING


@registry.variable(
    "application.group", _("Application group"), T.STRING, requires=[FACT_APPLICATION]
)
def application_group(request: PolicyRequest):
    app = _application(request)
    return (app.group or MISSING) if app else MISSING


@registry.variable(
    "application.meta_publisher",
    _("Application publisher"),
    T.STRING,
    requires=[FACT_APPLICATION],
)
def application_meta_publisher(request: PolicyRequest):
    app = _application(request)
    return (app.meta_publisher or MISSING) if app else MISSING
