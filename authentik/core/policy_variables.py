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
    attribute,
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


def _add_user_field(key: str, label, vtype, field: str | None = None, **kwargs):
    registry.add_variable(
        f"user.{key}", label, vtype, _USER, attribute(_user, field or key), **kwargs
    )


_add_user_field(
    "id",
    _("User"),
    T.model("authentik_core.user"),
    field="pk",
    description=_(
        "The user the policy is evaluated for. In flows, this is the user the flow is "
        "executed for, which can differ from the currently logged in user."
    ),
)
_add_user_field("username", _("Username"), T.STRING)
_add_user_field("name", _("Name"), T.STRING)
_add_user_field("email", _("Email"), T.STRING)
registry.add_variable(
    "user.is_active",
    _("Is active"),
    T.BOOLEAN,
    _USER,
    lambda request: (user := _user(request)) is not None and user.is_active,
)
registry.add_variable(
    "user.is_authenticated",
    _("Is authenticated"),
    T.BOOLEAN,
    _USER,
    lambda request: _user(request) is not None,
    description=_("False when the policy is evaluated for an anonymous user."),
)
_add_user_field("type", _("Type"), T.enum(UserTypes.choices))
_add_user_field("path", _("Path"), T.STRING)
_add_user_field("date_joined", _("Date joined"), T.DATETIME)
_add_user_field("last_login", _("Last login"), T.DATETIME)


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
    for attr in attributes:
        vtype = types.get(attr.type)
        if not vtype:
            continue
        label = f"{attr.group} › {attr.label}" if attr.group else attr.label
        yield KnownParam(
            key=attr.key,
            label=f"{_('Attribute')} › {label}",
            type=T.list(vtype) if attr.is_array else vtype,
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


for _key, _label, _blank in (
    ("slug", _("Application slug"), False),
    ("name", _("Application name"), False),
    ("group", _("Application group"), True),
    ("meta_publisher", _("Application publisher"), True),
):
    registry.add_variable(
        f"application.{_key}",
        _label,
        T.STRING,
        [FACT_APPLICATION],
        attribute(_application, _key, blank_missing=_blank),
    )


registry.add_variable(
    "user.has_usable_password",
    _("Has usable password"),
    T.BOOLEAN,
    _USER,
    lambda request: user.has_usable_password() if (user := _user(request)) else MISSING,
    description=_("False when the user has no password set, or it has been disabled."),
)


def _can_change(attribute: str, tenant_default: str):
    """Resolver checking the user's (group-)attributes for permission to change a field,
    falling back to the default configured on the tenant"""

    def resolve(request: PolicyRequest):
        user = _user(request)
        if not request.http_request or not user:
            return MISSING
        tenant = getattr(request.http_request, "tenant", None)
        default = getattr(tenant, tenant_default, MISSING)
        return user.group_attributes(request.http_request).get(attribute, default)

    return resolve


for _key, _attribute, _label, _description in (
    (
        "email",
        USER_ATTRIBUTE_CHANGE_EMAIL,
        _("Can change email"),
        _(
            "Whether the user is allowed to change their email address, based on their "
            "attributes, their groups' attributes and the system settings."
        ),
    ),
    (
        "name",
        USER_ATTRIBUTE_CHANGE_NAME,
        _("Can change name"),
        _(
            "Whether the user is allowed to change their name, based on their attributes, "
            "their groups' attributes and the system settings."
        ),
    ),
    (
        "username",
        USER_ATTRIBUTE_CHANGE_USERNAME,
        _("Can change username"),
        _(
            "Whether the user is allowed to change their username, based on their attributes, "
            "their groups' attributes and the system settings."
        ),
    ),
):
    registry.add_variable(
        f"user.can_change_{_key}",
        _label,
        T.BOOLEAN,
        [FACT_HTTP_REQUEST],
        _can_change(_attribute, f"default_user_change_{_key}"),
        description=_description,
    )
