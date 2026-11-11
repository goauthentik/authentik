"""Checking and creating the application an application request asks for"""

from collections.abc import Iterable
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from django.db.models import Model
from django.utils.text import slugify
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from authentik.common.oauth.constants import FORBIDDEN_URI_SCHEMES
from authentik.core.models import Application, Group
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)

if TYPE_CHECKING:
    from authentik.enterprise.requests.models import ApplicationTemplate, RequestedApplication

# Grant types that send the browser back to the client, so the client needs a redirect URI.
REDIRECTING_GRANT_TYPES = {GrantType.AUTHORIZATION_CODE, GrantType.IMPLICIT, GrantType.HYBRID}
# Start of a `%`-format placeholder, as `Application.get_launch_url` fills in.
PLACEHOLDER = "%("


def check_requested_application(
    template: ApplicationTemplate,
    client_type: str,
    redirect_uris: list[str],
    grant_types: list[str],
    groups: Iterable[Group],
    launch_url: str,
):
    """Raise a ValidationError, keyed by field, when `template` does not allow the requested
    application. Run when the request is made and again when it is approved, since the template
    may have changed in between."""
    errors = {}
    # Launch URLs, and the first redirect URI when there is none, are formatted with the viewing
    # user's data (`%(email)s`, `%(attributes)s`) for every member who opens the application's
    # tile. An admin may use that; a requester could send members' data to their own server.
    if PLACEHOLDER in launch_url:
        errors["meta_launch_url"] = _("Launch URLs cannot contain {placeholder}.").format(
            placeholder=PLACEHOLDER
        )
    bindable = set(template.bindable_groups.values_list("pk", flat=True))
    groups = list(groups)
    if not groups:
        errors["groups"] = _("Select at least one group.")
    elif not_bindable := sorted(group.name for group in groups if group.pk not in bindable):
        errors["groups"] = _("The template does not allow binding: {groups}").format(
            groups=", ".join(not_bindable)
        )
    if not grant_types:
        errors["grant_types"] = _("Select at least one grant type.")
    elif not_allowed := sorted(set(grant_types) - set(template.allowed_grant_types)):
        errors["grant_types"] = _("The template does not allow: {grant_types}").format(
            grant_types=", ".join(not_allowed)
        )
    elif GrantType.CLIENT_CREDENTIALS in grant_types and client_type != ClientType.CONFIDENTIAL:
        errors["grant_types"] = _("client_credentials requires a confidential client.")
    if REDIRECTING_GRANT_TYPES.intersection(grant_types) and not redirect_uris:
        errors["redirect_uris"] = _("{grant_types} require at least one redirect URI.").format(
            grant_types=", ".join(sorted(REDIRECTING_GRANT_TYPES.intersection(grant_types)))
        )
    for uri in redirect_uris:
        scheme = urlparse(uri).scheme.lower()
        if not scheme or scheme in FORBIDDEN_URI_SCHEMES:
            errors["redirect_uris"] = _(
                "Redirect URIs need a scheme other than {schemes}: {uri}"
            ).format(schemes=", ".join(sorted(FORBIDDEN_URI_SCHEMES)), uri=uri)
            break
        if PLACEHOLDER in uri:
            errors["redirect_uris"] = _("Redirect URIs cannot contain {placeholder}.").format(
                placeholder=PLACEHOLDER
            )
            break
    if errors:
        raise ValidationError(errors)


def _unique(model: type[Model], field: str, base: str, reserved: Iterable[str] = ()) -> str:
    """`base`, or `base-2`, `base-3`, ... whichever is free for `field` of `model` and not
    `reserved`."""
    candidate = base
    counter = 1
    while candidate in reserved or model.objects.filter(**{field: candidate}).exists():
        counter += 1
        candidate = f"{base}-{counter}"
    return candidate


def create_requested_application(requested: RequestedApplication) -> Application:
    """Create the provider, application and group bindings `requested` asks for, configured as
    its template says. Checks the request against the template first."""
    template = requested.template
    if not template:
        raise ValidationError(_("The application template of this request has been deleted."))
    groups = list(requested.groups.order_by("name"))
    check_requested_application(
        template,
        requested.client_type,
        requested.redirect_uris,
        requested.grant_types,
        groups,
        requested.meta_launch_url,
    )
    provider = OAuth2Provider(
        name=_unique(OAuth2Provider, "name", requested.name),
        client_type=requested.client_type,
        grant_types=requested.grant_types,
        authorization_flow=template.authorization_flow,
        invalidation_flow=template.invalidation_flow,
        signing_key=template.signing_key,
    )
    provider.redirect_uris = [
        RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url=uri)
        for uri in requested.redirect_uris
    ]
    provider.save()
    provider.property_mappings.set(template.property_mappings.all())
    application = Application.objects.create(
        name=requested.name,
        slug=_unique(
            Application,
            "slug",
            slugify(requested.name) or "application",
            reserved=Application.reserved_slugs,
        ),
        provider=provider,
        group=template.application_group,
        meta_description=requested.meta_description,
        meta_launch_url=requested.meta_launch_url,
    )
    PolicyBinding.objects.bulk_create(
        PolicyBinding(target=application, group=group, order=order)
        for order, group in enumerate(groups)
    )
    requested.application = application
    requested.provider = provider
    requested.save()
    return application
