"""Policy variables provided by core"""

from collections.abc import Iterator
from time import monotonic

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from guardian.conf import settings as guardian_settings

from authentik.core.models import (
    USER_ATTRIBUTE_CHANGE_EMAIL,
    USER_ATTRIBUTE_CHANGE_NAME,
    USER_ATTRIBUTE_CHANGE_USERNAME,
    Application,
    ObjectAttribute,
    User,
    UserTypes,
)
from authentik.policies.conditional.registry import (
    FACT_HTTP_REQUEST,
    FACT_USER,
    KnownParam,
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
registry.scenario(
    "application_authorization",
    [FACT_HTTP_REQUEST, FACT_APPLICATION],
    models=["authentik_core.application"],
    label=_("Application authorization"),
    description=_("Deciding whether a user can access an application."),
)

_USER = [FACT_USER]


def _user(request: PolicyRequest) -> User | None:
    """The user the policy is evaluated for, or None for anonymous users. Policies can be
    evaluated for Django's `AnonymousUser`, or for guardian's anonymous user object."""
    user = request.user
    if not isinstance(user, User) or not user.pk:
        return None
    if user.username == guardian_settings.ANONYMOUS_USER_NAME:
        return None
    return user


def _field(request: PolicyRequest, name: str):
    user = _user(request)
    if not user:
        return MISSING
    value = getattr(user, name)
    # Empty text is a value, for example a user without an email address
    return MISSING if value is None else value


@registry.variable(
    "user.id",
    _("User"),
    T.model("authentik_core.user"),
    requires=_USER,
    description=_(
        "The user the policy is evaluated for. In flows, this is the user the flow is "
        "executed for, which can differ from the currently logged in user."
    ),
)
def user_id(request: PolicyRequest):
    return _field(request, "pk")


@registry.variable("user.username", _("Username"), T.STRING, requires=_USER)
def user_username(request: PolicyRequest):
    return _field(request, "username")


@registry.variable("user.name", _("Name"), T.STRING, requires=_USER)
def user_name(request: PolicyRequest):
    return _field(request, "name")


@registry.variable("user.email", _("Email"), T.STRING, requires=_USER)
def user_email(request: PolicyRequest):
    return _field(request, "email")


@registry.variable("user.is_active", _("Is active"), T.BOOLEAN, requires=_USER)
def user_is_active(request: PolicyRequest):
    user = _user(request)
    return user.is_active if user else False


@registry.variable(
    "user.is_authenticated",
    _("Is authenticated"),
    T.BOOLEAN,
    requires=_USER,
    description=_("False when the policy is evaluated for an anonymous user."),
)
def user_is_authenticated(request: PolicyRequest):
    return _user(request) is not None


@registry.variable("user.type", _("Type"), T.enum(UserTypes.choices), requires=_USER)
def user_type(request: PolicyRequest):
    return _field(request, "type")


@registry.variable("user.path", _("Path"), T.STRING, requires=_USER)
def user_path(request: PolicyRequest):
    return _field(request, "path")


@registry.variable("user.date_joined", _("Date joined"), T.DATETIME, requires=_USER)
def user_date_joined(request: PolicyRequest):
    return _field(request, "date_joined")


@registry.variable("user.last_login", _("Last login"), T.DATETIME, requires=_USER)
def user_last_login(request: PolicyRequest):
    return _field(request, "last_login")


@registry.variable(
    "user.groups",
    _("Groups"),
    T.list(T.model("authentik_core.group")),
    requires=_USER,
    description=_("Groups the user is a member of, including inherited groups."),
)
def user_groups(request: PolicyRequest):
    user = _user(request)
    if not user:
        return []
    return list(user.all_groups().values_list("pk", flat=True))


# Object attributes rarely change, but are needed when compiling policies which use them.
# Keep them in memory for a short time, and clear them when they're changed in this process.
OBJECT_ATTRIBUTE_PARAMS_TIMEOUT = 60
_object_attribute_params: dict[str, tuple[float, tuple[KnownParam, ...]]] = {}


@receiver(post_save, sender=ObjectAttribute)
@receiver(post_delete, sender=ObjectAttribute)
def clear_object_attribute_params(**_):
    _object_attribute_params.clear()


def object_attribute_params(model: str) -> tuple[KnownParam, ...]:
    """Well-defined parameters for the `attributes` of `model` (`app_label.model_name`), from
    the enabled object attributes defined for it"""
    cached = _object_attribute_params.get(model)
    if cached and cached[0] > monotonic():
        return cached[1]
    params = tuple(_load_object_attribute_params(model))
    _object_attribute_params[model] = (monotonic() + OBJECT_ATTRIBUTE_PARAMS_TIMEOUT, params)
    return params


def _load_object_attribute_params(model: str) -> Iterator[KnownParam]:
    app_label, model_name = model.split(".")
    types = {
        ObjectAttribute.AttributeType.TEXT: T.STRING,
        ObjectAttribute.AttributeType.NUMBER: T.NUMBER,
        ObjectAttribute.AttributeType.BOOLEAN: T.BOOLEAN,
    }
    attributes = ObjectAttribute.objects.filter(
        enabled=True, object_type__app_label=app_label, object_type__model=model_name
    ).order_by("group", "label")
    for attribute in attributes:
        vtype = types.get(attribute.type)
        if not vtype:
            continue
        label = f"{attribute.group} › {attribute.label}" if attribute.group else attribute.label
        yield KnownParam(
            key=attribute.key,
            label=f"{_('Attribute')} › {label}",
            type=T.list(vtype) if attribute.is_array else vtype,
        )


@registry.variable(
    "user.attributes",
    _("Attribute"),
    T.ANY,
    requires=_USER,
    param=ParamKind.PATH,
    params=lambda: object_attribute_params("authentik_core.user"),
    description=_("Value of the user's attributes at the given dotted path."),
)
def user_attributes(request: PolicyRequest, path: str):
    user = _user(request)
    return dig(user.attributes, path) if user else MISSING


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


@registry.variable(
    "user.has_usable_password",
    _("Has usable password"),
    T.BOOLEAN,
    requires=_USER,
    description=_("False when the user has no password set, or it has been disabled."),
)
def user_has_usable_password(request: PolicyRequest):
    user = _user(request)
    return user.has_usable_password() if user else MISSING


def _can_change(request: PolicyRequest, attribute: str, tenant_default: str):
    """Check the user's (group-)attributes for permission to change a field, falling back
    to the default configured on the tenant"""
    user = _user(request)
    if not request.http_request or not user:
        return MISSING
    default = getattr(getattr(request.http_request, "tenant", None), tenant_default, MISSING)
    return user.group_attributes(request.http_request).get(attribute, default)


@registry.variable(
    "user.can_change_email",
    _("Can change email"),
    T.BOOLEAN,
    requires=[FACT_HTTP_REQUEST],
    description=_(
        "Whether the user is allowed to change their email address, based on their "
        "attributes, their groups' attributes and the system settings."
    ),
)
def user_can_change_email(request: PolicyRequest):
    return _can_change(request, USER_ATTRIBUTE_CHANGE_EMAIL, "default_user_change_email")


@registry.variable(
    "user.can_change_name",
    _("Can change name"),
    T.BOOLEAN,
    requires=[FACT_HTTP_REQUEST],
    description=_(
        "Whether the user is allowed to change their name, based on their attributes, "
        "their groups' attributes and the system settings."
    ),
)
def user_can_change_name(request: PolicyRequest):
    return _can_change(request, USER_ATTRIBUTE_CHANGE_NAME, "default_user_change_name")


@registry.variable(
    "user.can_change_username",
    _("Can change username"),
    T.BOOLEAN,
    requires=[FACT_HTTP_REQUEST],
    description=_(
        "Whether the user is allowed to change their username, based on their attributes, "
        "their groups' attributes and the system settings."
    ),
)
def user_can_change_username(request: PolicyRequest):
    return _can_change(request, USER_ATTRIBUTE_CHANGE_USERNAME, "default_user_change_username")
