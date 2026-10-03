"""Policy variables provided by core"""

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
from authentik.lib.utils.dict import get_path_from_dict
from authentik.policies.conditional.registry import (
    FACT_HTTP_REQUEST,
    FACT_USER,
    KnownParam,
    ParamKind,
    Variable,
    registry,
)
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.types import PolicyRequest

FACT_APPLICATION = "application"

registry.scenario(
    "application_authorization",
    [FACT_HTTP_REQUEST, FACT_APPLICATION],
    models=["authentik_core.application"],
    label=_("Application authorization"),
    description=_("Deciding whether a user can access an application."),
)


def _user(request: PolicyRequest) -> User | None:
    """The user the policy is evaluated for, or None for anonymous users. Policies can be
    evaluated for Django's `AnonymousUser`, or for guardian's anonymous user object."""
    user = request.user
    if not isinstance(user, User) or not user.pk:
        return None
    return None if user.username == guardian_settings.ANONYMOUS_USER_NAME else user


registry.variable(
    "user.id",
    _("User"),
    T.model("authentik_core.user"),
    [FACT_USER],
    description=_(
        "The user the policy is evaluated for. In flows, this is the user the flow is "
        "executed for, which can differ from the currently logged in user."
    ),
)(Variable.attribute(_user, "pk"))
for _field, _label, _type in (
    ("username", _("Username"), T.STRING),
    ("name", _("Name"), T.STRING),
    ("email", _("Email"), T.STRING),
    ("type", _("Type"), T.enum(UserTypes.choices)),
    ("path", _("Path"), T.STRING),
    ("date_joined", _("Date joined"), T.DATETIME),
    ("last_login", _("Last login"), T.DATETIME),
):
    registry.variable(f"user.{_field}", _label, _type, [FACT_USER])(
        Variable.attribute(_user, _field)
    )
registry.variable("user.is_active", _("Is active"), T.BOOLEAN, [FACT_USER])(
    lambda request: bool(user := _user(request)) and user.is_active
)
registry.variable(
    "user.is_authenticated",
    _("Is authenticated"),
    T.BOOLEAN,
    [FACT_USER],
    description=_("False when the policy is evaluated for an anonymous user."),
)(lambda request: _user(request) is not None)
registry.variable(
    "user.has_usable_password",
    _("Has usable password"),
    T.BOOLEAN,
    [FACT_USER],
    description=_("False when the user has no password set, or it has been disabled."),
)(lambda request: user.has_usable_password() if (user := _user(request)) else MISSING)


@registry.variable(
    "user.groups",
    _("Groups"),
    T.list(T.model("authentik_core.group")),
    [FACT_USER],
    description=_("Groups the user is a member of, including inherited groups."),
)
def user_groups(request: PolicyRequest):
    user = _user(request)
    return list(user.all_groups().values_list("pk", flat=True)) if user else []


# Object attributes rarely change, but are needed when compiling policies which use them.
# Keep them in memory for a short time, and clear them when they're changed in this process.
OBJECT_ATTRIBUTE_PARAMS_TIMEOUT = 60
_user_attribute_params: tuple[float, tuple[KnownParam, ...]] = (0, ())


@receiver(post_save, sender=ObjectAttribute)
@receiver(post_delete, sender=ObjectAttribute)
def clear_user_attribute_params(**_):
    global _user_attribute_params  # noqa: PLW0603
    _user_attribute_params = (0, ())


def user_attribute_params() -> tuple[KnownParam, ...]:
    """Well-defined user attributes, from the enabled object attributes defined for users"""
    global _user_attribute_params  # noqa: PLW0603
    if _user_attribute_params[0] > monotonic():
        return _user_attribute_params[1]
    types = {
        ObjectAttribute.AttributeType.TEXT: T.STRING,
        ObjectAttribute.AttributeType.NUMBER: T.NUMBER,
        ObjectAttribute.AttributeType.BOOLEAN: T.BOOLEAN,
    }
    attributes = ObjectAttribute.objects.filter(
        enabled=True,
        object_type__app_label="authentik_core",
        object_type__model="user",
        type__in=types,
    ).order_by("group", "label")
    params = tuple(
        KnownParam(
            attribute.key,
            " › ".join(filter(None, [str(_("Attribute")), attribute.group, attribute.label])),
            T.list(types[attribute.type]) if attribute.is_array else types[attribute.type],
        )
        for attribute in attributes
    )
    _user_attribute_params = (monotonic() + OBJECT_ATTRIBUTE_PARAMS_TIMEOUT, params)
    return params


registry.variable(
    "user.attributes",
    _("Attribute"),
    T.ANY,
    [FACT_USER],
    param=ParamKind.PATH,
    known_params=user_attribute_params,
    description=_("Value of the user's attributes at the given dotted path."),
)(
    lambda request, path: (
        get_path_from_dict(user.attributes, path, default=MISSING)
        if (user := _user(request))
        else MISSING
    )
)


def _application(request: PolicyRequest) -> Application | None:
    return request.obj if isinstance(request.obj, Application) else None


for _field, _label in (
    ("slug", _("Application slug")),
    ("name", _("Application name")),
    ("group", _("Application group")),
    ("meta_publisher", _("Application publisher")),
):
    registry.variable(f"application.{_field}", _label, T.STRING, [FACT_APPLICATION])(
        Variable.attribute(_application, _field, blank_missing=True)
    )


def _can_change(attribute: str, tenant_default: str):
    """Whether the user is allowed to change a field, based on their (group-)attributes,
    falling back to the default configured on the tenant"""

    def resolve(request: PolicyRequest):
        user = _user(request)
        if not request.http_request or not user:
            return MISSING
        default = getattr(getattr(request.http_request, "tenant", None), tenant_default, MISSING)
        return user.group_attributes(request.http_request).get(attribute, default)

    return resolve


for _field, _attribute, _label in (
    ("email", USER_ATTRIBUTE_CHANGE_EMAIL, _("Can change email")),
    ("name", USER_ATTRIBUTE_CHANGE_NAME, _("Can change name")),
    ("username", USER_ATTRIBUTE_CHANGE_USERNAME, _("Can change username")),
):
    registry.variable(
        f"user.can_change_{_field}",
        _label,
        T.BOOLEAN,
        [FACT_HTTP_REQUEST],
        description=_(
            "Whether the user is allowed to change this field, based on their attributes, "
            "their groups' attributes and the system settings."
        ),
    )(_can_change(_attribute, f"default_user_change_{_field}"))
