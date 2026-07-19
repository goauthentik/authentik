"""authentik OAuth2 Dynamic Client Registration (RFC 7591)"""

import json
import time
from typing import Any

from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views import View
from structlog.stdlib import get_logger

from authentik.api.authentication import validate_auth
from authentik.common.oauth.constants import SCOPE_AUTHENTIK_DCR
from authentik.core.models import Application, User
from authentik.lib.generators import generate_id
from authentik.policies.engine import PolicyEngine
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientType,
    GrantType,
    OAuth2DynamicClientRegistration,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    generate_client_secret,
)

LOGGER = get_logger()

AUTH_METHOD_TO_CLIENT_TYPE = {
    "client_secret_basic": ClientType.CONFIDENTIAL,
    "client_secret_post": ClientType.CONFIDENTIAL,
    "none": ClientType.PUBLIC,
}


def _dcr_error(error: str, description: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": error, "error_description": description}, status=status)


class DynamicClientRegistrationView(View):
    """RFC 7591 Dynamic Client Registration endpoint.

    POST /application/o/<application_slug>/register/
    """

    dcr: OAuth2DynamicClientRegistration

    def _authenticate_access_token(self, request: HttpRequest) -> AccessToken | None:
        """Authenticate the request via a Bearer `AccessToken` carrying the
        `goauthentik.io/oidc/dcr` scope, mirroring how `SCOPE_AUTHENTIK_API`
        authenticates access to authentik's own API."""
        raw_token = validate_auth(request.headers.get("Authorization", "").encode())
        if not raw_token:
            return None
        access_token = AccessToken.objects.filter(
            token=raw_token, _scope__icontains=SCOPE_AUTHENTIK_DCR
        ).first()
        if not access_token or SCOPE_AUTHENTIK_DCR not in access_token.scope:
            return None
        return access_token

    def _check_policy_access(self, request: HttpRequest, user: User) -> bool:
        engine = PolicyEngine(self.dcr, user, request)
        engine.use_cache = False
        engine.build()
        return engine.result.passing

    def _unique_app_slug(self, base: str) -> str:
        slug = slugify(base)[:200] or "client"
        candidate = slug
        counter = 1
        while Application.objects.filter(slug=candidate).exists():
            candidate = f"{slug}-{counter}"
            counter += 1
        return candidate

    @transaction.atomic
    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        # --- Access control -----------------------------------------------
        access_token = self._authenticate_access_token(request)
        if access_token is None:
            return _dcr_error(
                "invalid_token",
                "A valid access token with the "
                f"'{SCOPE_AUTHENTIK_DCR}' scope is required to register clients.",
                status=401,
            )

        if not self._check_policy_access(request, access_token.user):
            LOGGER.info("DCR registration rejected by policy", slug=application_slug)
            return _dcr_error(
                "access_denied", "Policy check failed for client registration.", status=403
            )

        # --- Parse request body ------------------------------------------
        try:
            metadata: dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError, UnicodeDecodeError:
            return _dcr_error("invalid_client_metadata", "Request body must be valid JSON.")

        if not isinstance(metadata, dict):
            return _dcr_error("invalid_client_metadata", "Request body must be a JSON object.")

        raw_uris = metadata.get("redirect_uris")
        if not raw_uris or not isinstance(raw_uris, list):
            return _dcr_error(
                "invalid_redirect_uri", "redirect_uris is required and must be a non-empty list."
            )
        if not all(isinstance(u, str) for u in raw_uris):
            return _dcr_error("invalid_redirect_uri", "All redirect_uris must be strings.")

        redirect_uris = [
            RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url=uri) for uri in raw_uris
        ]

        # --- Resolve settings --------------------------------------------
        auth_method = metadata.get("token_endpoint_auth_method", "client_secret_basic")
        client_type = AUTH_METHOD_TO_CLIENT_TYPE.get(auth_method, ClientType.CONFIDENTIAL)

        requested_grants = metadata.get("grant_types", [GrantType.AUTHORIZATION_CODE])
        if not isinstance(requested_grants, list):
            return _dcr_error("invalid_client_metadata", "grant_types must be an array.")
        if self.dcr.allowed_grant_types:
            requested_grants = [g for g in requested_grants if g in self.dcr.allowed_grant_types]
        grant_types = [g for g in requested_grants if g in GrantType.values] or [
            GrantType.AUTHORIZATION_CODE
        ]

        client_name = metadata.get("client_name", "")

        # --- Create OAuth2Provider ---------------------------------------
        provider = OAuth2Provider(
            name=client_name or generate_id(),
            client_id=generate_id(),
            client_secret=generate_client_secret(),
            client_type=client_type,
            grant_types=grant_types,
            authorization_flow=self.dcr.default_authorization_flow,
            invalidation_flow=self.dcr.default_invalidation_flow,
            access_token_validity=self.dcr.access_token_validity,
            refresh_token_validity=self.dcr.refresh_token_validity,
        )
        provider._redirect_uris = [
            {
                "matching_mode": uri.matching_mode,
                "url": uri.url,
                "redirect_uri_type": uri.redirect_uri_type,
            }
            for uri in redirect_uris
        ]
        provider.save()

        if self.dcr.default_property_mappings.exists():
            provider.property_mappings.set(self.dcr.default_property_mappings.all())

        # --- Optionally create Application --------------------------------
        if self.dcr.create_application:
            app_slug = self._unique_app_slug(client_name or provider.client_id)
            Application.objects.create(
                name=client_name or provider.client_id,
                slug=app_slug,
                provider=provider,
                group=self.dcr.default_application_group,
            )

        LOGGER.info(
            "DCR: registered new client",
            client_id=provider.client_id,
            client_name=provider.name,
            registered_by=access_token.user.username,
        )

        # --- RFC 7591 §3.2.1 response -------------------------------------
        response_data: dict[str, Any] = {
            "client_id": provider.client_id,
            "client_id_issued_at": int(time.time()),
            "redirect_uris": raw_uris,
            "grant_types": grant_types,
            "token_endpoint_auth_method": (
                auth_method if auth_method in AUTH_METHOD_TO_CLIENT_TYPE else "client_secret_basic"
            ),
        }

        if client_type == ClientType.CONFIDENTIAL:
            response_data["client_secret"] = provider.client_secret
            response_data["client_secret_expires_at"] = 0

        if client_name:
            response_data["client_name"] = client_name

        return JsonResponse(response_data, status=201)

    def dispatch(
        self, request: HttpRequest, application_slug: str, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        application = get_object_or_404(Application, slug=application_slug)
        provider = get_object_or_404(OAuth2Provider, pk=application.provider_id)

        try:
            self.dcr = OAuth2DynamicClientRegistration.objects.get(provider=provider)
        except OAuth2DynamicClientRegistration.DoesNotExist:
            return JsonResponse(
                {
                    "error": "not_found",
                    "error_description": (
                        "Dynamic client registration is not enabled for this provider."
                    ),
                },
                status=404,
            )

        return super().dispatch(request, application_slug, *args, **kwargs)
