"""AT Protocol OAuth Views"""

from time import time
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse, urlunparse

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.hashes import SHA256, Hash
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_pem_private_key,
)
from django.templatetags.static import static
from django.urls import reverse
from django.utils.crypto import constant_time_compare, get_random_string
from jwt import encode
from jwt.algorithms import ECAlgorithm
from jwt.utils import base64url_encode
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik.lib.generators import generate_id
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.sources.oauth.clients.base import BaseOAuthClient
from authentik.sources.oauth.models import OAuthSource, PKCEMethod
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()

# Bluesky defaults. AT Protocol OAuth requires these endpoint roles, but
# non-Bluesky deployments can use different hosts through the source URL fields.
BSKY_AUTHORIZATION_URL_DEFAULT = "https://bsky.social/oauth/authorize"
BSKY_TOKEN_URL_DEFAULT = "https://bsky.social/oauth/token"  # nosec
BSKY_PAR_URL_DEFAULT = "https://bsky.social/oauth/par"
BSKY_ISSUER_DEFAULT = "https://bsky.social"
BSKY_PUBLIC_PROFILE_URL_DEFAULT = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile"
HTTP_STATUS_BAD_REQUEST = 400

SESSION_KEY_ATPROTO = "authentik/sources/oauth/atproto"


class AtProtoOAuthClient(BaseOAuthClient):
    """AT Protocol OAuth client.

    AT Protocol looks like OAuth2 from a distance, but the required security
    profile is different enough that sharing the generic OAuth2 client would
    hide important behavior: PAR is mandatory, access tokens are DPoP-bound,
    public clients use metadata URLs instead of secrets, and the token subject
    is the user's DID rather than an OIDC userinfo subject.
    """

    def get_client_id(self) -> str:
        """Return the public client metadata URL."""
        return self.source.consumer_key

    @property
    def session_key(self) -> str:
        return f"{SESSION_KEY_ATPROTO}/{self.source.slug}"

    def get_authorization_url(self) -> str:
        if self.source.source_type.urls_customizable and self.source.authorization_url:
            return self.source.authorization_url
        return self.source.source_type.authorization_url or BSKY_AUTHORIZATION_URL_DEFAULT

    def get_token_url(self) -> str:
        if self.source.source_type.urls_customizable and self.source.access_token_url:
            return self.source.access_token_url
        return self.source.source_type.access_token_url or BSKY_TOKEN_URL_DEFAULT

    def get_par_url(self) -> str:
        if self.source.source_type.urls_customizable and self.source.request_token_url:
            return self.source.request_token_url
        return self.source.source_type.request_token_url or BSKY_PAR_URL_DEFAULT

    def get_issuer(self) -> str:
        parsed_url = urlparse(self.get_authorization_url())
        if parsed_url.scheme and parsed_url.netloc:
            return f"{parsed_url.scheme}://{parsed_url.netloc}"
        return BSKY_ISSUER_DEFAULT

    def get_redirect_args(self) -> dict[str, str]:
        """AT Protocol redirects are built from PAR responses instead."""
        raise NotImplementedError

    def get_redirect_url(self, parameters=None):
        """Create a PAR request and redirect with request_uri."""
        request_uri = self.create_pushed_authorization_request(parameters or {})
        parsed_url = urlparse(self.get_authorization_url())
        parsed_args = parse_qs(parsed_url.query)
        args = {
            "client_id": self.get_client_id(),
            "request_uri": request_uri,
        }
        args.update(parsed_args)
        params = urlencode(args, quote_via=quote, doseq=True)
        return urlunparse(parsed_url._replace(query=params))

    def create_pushed_authorization_request(self, parameters: dict[str, Any]) -> str:
        """Create the pushed authorization request and persist session data."""
        state = get_random_string(32)
        code_verifier = generate_id(length=128)
        private_key = ec.generate_private_key(ec.SECP256R1())
        login_hint = parameters.pop("login_hint", None)
        scope = parameters.pop("scope", [])
        if isinstance(scope, str):
            scopes = scope.split()
        else:
            scopes = list(scope)
        if "atproto" not in scopes:
            scopes.append("atproto")

        # The DPoP key and PKCE verifier must survive the browser redirect so
        # the callback can prove it is the same client that created the PAR.
        session_data = {
            "state": state,
            "code_verifier": code_verifier,
            "issuer": self.get_issuer(),
            "private_key": private_key.private_bytes(
                Encoding.PEM,
                PrivateFormat.PKCS8,
                NoEncryption(),
            ).decode(),
            "dpop_nonce": None,
            "login_hint": login_hint,
            "expected_did": self.resolve_identifier(login_hint) if login_hint else None,
        }
        self.request.session[self.session_key] = session_data

        # AT Protocol starts the browser flow with a PAR request. The browser
        # only receives a request_uri, not the full authorization parameters.
        body = {
            "client_id": self.get_client_id(),
            "response_type": "code",
            "redirect_uri": self.request.build_absolute_uri(self.callback),
            "scope": " ".join(sorted(set(scopes))),
            "state": state,
            "code_challenge": pkce_s256_challenge(code_verifier),
            "code_challenge_method": PKCEMethod.S256,
        }
        if login_hint:
            body["login_hint"] = login_hint
        body.update(parameters)
        response = self.request_with_dpop("post", self.get_par_url(), data=body)
        try:
            request_uri = response.json().get("request_uri")
        except ValueError as exc:
            raise RequestException("PAR response was not valid JSON", response=response) from exc
        if not request_uri:
            raise RequestException("PAR response did not include request_uri", response=response)
        return request_uri

    def get_access_token(self, **request_kwargs) -> dict[str, Any] | None:
        """Fetch the initial access token from the callback code."""
        session_data = self.request.session.get(self.session_key)
        if not session_data:
            LOGGER.warning("No AT Protocol OAuth session found")
            return {"error": "No AT Protocol OAuth session found."}
        if not constant_time_compare(session_data["state"], self.get_request_arg("state", "")):
            LOGGER.warning("AT Protocol OAuth state check failed")
            return {"error": "State check failed."}
        issuer = self.get_request_arg("iss")
        if not issuer or not constant_time_compare(session_data["issuer"], issuer):
            LOGGER.warning("AT Protocol OAuth issuer check failed", issuer=issuer)
            return {"error": "Issuer check failed."}
        code = self.get_request_arg("code")
        if not code:
            return {"error": self.get_request_arg("error_description") or "No token received."}

        data = {
            "grant_type": "authorization_code",
            "client_id": self.get_client_id(),
            "redirect_uri": self.request.build_absolute_uri(self.callback),
            "code": code,
            "code_verifier": session_data["code_verifier"],
        }
        try:
            response = self.request_with_dpop("post", self.get_token_url(), data=data)
            token = response.json()
        except ValueError as exc:
            LOGGER.warning("AT Protocol token response was not valid JSON", exc=exc)
            return None
        except RequestException as exc:
            LOGGER.warning(
                "Unable to fetch AT Protocol access token",
                exc=exc,
                response=exc.response.text if exc.response is not None else str(exc),
            )
            return None

        validation_error = self.validate_token_response(token, session_data, issuer)
        if validation_error:
            return {"error": validation_error}
        return token

    def validate_token_response(
        self,
        token: dict[str, Any],
        session_data: dict[str, Any],
        issuer: str,
    ) -> str | None:
        """Validate AT Protocol token claims and attach the verified PDS URL."""
        # The token response identifies the account by DID. That DID becomes
        # the stable source connection identifier in authentik.
        did = token.get("sub")
        if not did:
            return "Token response did not include an account DID."
        if "atproto" not in token.get("scope", "").split():
            return "Token response did not include the atproto scope."
        if token.get("token_type") != "DPoP":
            return "Token response did not include a DPoP token type."
        expected_did = session_data.get("expected_did")
        if expected_did and not constant_time_compare(expected_did, did):
            LOGGER.warning("AT Protocol OAuth subject check failed", expected=expected_did, did=did)
            return "Subject check failed."
        # Verify the DID document's PDS points back to the authorization server
        # that issued the callback, otherwise a token could claim another DID.
        pds_url = self.get_pds_url_for_subject(did, issuer)
        if not pds_url:
            return "Issuer is not authoritative for this account."
        token["pds_url"] = pds_url
        return None

    def get_profile_info(self, token: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch public profile data for the authenticated DID."""
        did = token.get("sub")
        if not did:
            return None
        profile_url = BSKY_PUBLIC_PROFILE_URL_DEFAULT
        if self.source.source_type.urls_customizable and self.source.profile_url:
            profile_url = self.source.profile_url
        response = self.session.get(profile_url, params={"actor": did})
        try:
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning(
                "Unable to fetch AT Protocol profile",
                exc=exc,
                response=exc.response.text if exc.response is not None else str(exc),
            )
            return {"did": did}
        profile = response.json()
        profile["did"] = did
        if "transition:email" in token.get("scope", "").split() and token.get("pds_url"):
            profile.update(self.get_session_info(token))
        return profile

    def request_with_dpop(self, method: str, url: str, **kwargs):
        """Make a DPoP request, retrying once when the server provides a fresh nonce."""
        response = self.do_dpop_request(method, url, **kwargs)
        if response.status_code == HTTP_STATUS_BAD_REQUEST and response.headers.get("DPoP-Nonce"):
            self.update_dpop_nonce(response.headers["DPoP-Nonce"])
            response = self.do_dpop_request(method, url, **kwargs)
        response.raise_for_status()
        nonce = response.headers.get("DPoP-Nonce")
        if not nonce:
            raise RequestException("DPoP response did not include DPoP-Nonce", response=response)
        self.update_dpop_nonce(nonce)
        return response

    def get_session_info(self, token: dict[str, Any]) -> dict[str, Any]:
        """Fetch private session data when transition:email was granted."""
        pds_url = token["pds_url"].rstrip("/")
        session_url = f"{pds_url}/xrpc/com.atproto.server.getSession"
        headers = {
            "Authorization": f"DPoP {token['access_token']}",
        }
        response = self.do_dpop_request(
            "get",
            session_url,
            headers=headers,
            access_token=token["access_token"],
        )
        if response.status_code == HTTP_STATUS_BAD_REQUEST and response.headers.get("DPoP-Nonce"):
            self.update_dpop_nonce(response.headers["DPoP-Nonce"])
            response = self.do_dpop_request(
                "get",
                session_url,
                headers=headers,
                access_token=token["access_token"],
            )
        try:
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning(
                "Unable to fetch AT Protocol session info",
                exc=exc,
                response=exc.response.text if exc.response is not None else str(exc),
            )
            return {}
        nonce = response.headers.get("DPoP-Nonce")
        if nonce:
            self.update_dpop_nonce(nonce)
        try:
            return response.json()
        except ValueError as exc:
            LOGGER.warning("AT Protocol session response was not valid JSON", exc=exc)
            return {}

    def do_dpop_request(self, method: str, url: str, **kwargs):
        access_token = kwargs.pop("access_token", None)
        headers = dict(kwargs.pop("headers", {}))
        headers["Accept"] = "application/json"
        headers["DPoP"] = self.build_dpop_proof(method, url, access_token)
        return self.session.request(method, url, headers=headers, **kwargs)

    def build_dpop_proof(self, method: str, url: str, access_token: str | None = None) -> str:
        session_data = self.request.session[self.session_key]
        private_key = load_pem_private_key(session_data["private_key"].encode(), password=None)
        if not isinstance(private_key, EllipticCurvePrivateKey):
            raise TypeError("DPoP private key must be an EC key")
        payload = {
            "jti": generate_id(),
            "htm": method.upper(),
            "htu": url,
            "iat": int(time()),
        }
        if session_data.get("dpop_nonce"):
            payload["nonce"] = session_data["dpop_nonce"]
        if access_token:
            # Resource requests bind the proof to the access token with ath.
            digest = Hash(SHA256())
            digest.update(access_token.encode())
            payload["ath"] = base64url_encode(digest.finalize()).decode()
        public_jwk = ECAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
        public_jwk.pop("kid", None)
        return encode(
            payload,
            private_key,
            algorithm="ES256",
            headers={
                "typ": "dpop+jwt",
                "jwk": public_jwk,
            },
        )

    def update_dpop_nonce(self, nonce: str) -> None:
        session_data = self.request.session[self.session_key]
        session_data["dpop_nonce"] = nonce
        self.request.session[self.session_key] = session_data

    def get_request_arg(self, key: str, default: Any | None = None) -> Any:
        if self.request.method == "POST":
            return self.request.POST.get(key, default)
        return self.request.GET.get(key, default)

    def resolve_identifier(self, identifier: str | None) -> str | None:
        """Resolve a handle or DID to a DID."""
        if not identifier:
            return None
        if identifier.startswith("did:"):
            return identifier
        response = self.session.get(
            f"{self.get_issuer()}/xrpc/com.atproto.identity.resolveHandle",
            params={"handle": identifier.removeprefix("@")},
        )
        try:
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning(
                "Unable to resolve AT Protocol login hint",
                identifier=identifier,
                exc=exc,
            )
            return None
        try:
            return response.json().get("did")
        except ValueError as exc:
            LOGGER.warning("AT Protocol handle resolution response was not valid JSON", exc=exc)
            return None

    def get_pds_url_for_subject(self, did: str, issuer: str) -> str | None:
        """Verify that the DID's PDS resolves to the callback issuer."""
        try:
            did_document = self.get_did_document(did)
            pds_url = self.get_pds_url(did_document)
            if not pds_url:
                LOGGER.warning("DID document does not include an atproto PDS", did=did)
                return None
            resource_metadata = self.session.get(
                f"{pds_url.rstrip('/')}/.well-known/oauth-protected-resource"
            )
            resource_metadata.raise_for_status()
            try:
                authorization_servers = resource_metadata.json().get("authorization_servers", [])
            except ValueError as exc:
                raise RequestException(
                    "OAuth protected resource metadata was not valid JSON",
                    response=resource_metadata,
                ) from exc
        except RequestException as exc:
            LOGGER.warning("Unable to verify AT Protocol issuer", did=did, issuer=issuer, exc=exc)
            return None
        if issuer in authorization_servers:
            return pds_url
        return None

    def get_did_document(self, did: str) -> dict[str, Any]:
        if did.startswith("did:plc:"):
            response = self.session.get(f"https://plc.directory/{did}")
        elif did.startswith("did:web:"):
            # did:web resolves by fetching a DID document from the hostname in the DID.
            # The AT Protocol local simulator uses did:web:localhost, which cannot use
            # HTTPS locally; real did:web identities should resolve over HTTPS.
            did_parts = [unquote(part) for part in did.removeprefix("did:web:").split(":")]
            host = did_parts[0]
            path = "/".join(did_parts[1:])
            scheme = "http" if host.startswith(("localhost", "127.0.0.1")) else "https"
            did_path = f"{path}/did.json" if path else ".well-known/did.json"
            response = self.session.get(f"{scheme}://{host}/{did_path}")
        else:
            raise RequestException(f"Unsupported DID method: {did}")
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as exc:
            raise RequestException("DID document was not valid JSON", response=response) from exc

    def get_pds_url(self, did_document: dict[str, Any]) -> str | None:
        for service in did_document.get("service", []):
            if service.get("id") == "#atproto_pds":
                return service.get("serviceEndpoint")
            if service.get("type") == "AtprotoPersonalDataServer":
                return service.get("serviceEndpoint")
        return None


class AtProtoOAuthRedirect(OAuthRedirect):
    """AT Protocol OAuth redirect."""

    client_class = AtProtoOAuthClient

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["atproto"],
        }


class AtProtoOAuthCallback(OAuthCallback):
    """AT Protocol OAuth callback."""

    client_class = AtProtoOAuthClient

    def get_callback_url(self, source: OAuthSource) -> str:
        return reverse(
            "authentik_sources_oauth:oauth-client-callback",
            kwargs={"source_slug": source.slug},
        )

    def get_user_id(self, info: dict[str, Any]) -> str | None:
        return info.get("did")


@registry.register()
class AtProtoType(SourceType):
    """AT Protocol Type definition"""

    callback_view = AtProtoOAuthCallback
    redirect_view = AtProtoOAuthRedirect
    verbose_name = "AT Protocol"
    name = "atproto"

    # Defaults target Bluesky. They are editable because other AT Protocol
    # authorization servers can expose the same endpoint roles on different URLs.
    authorization_url = BSKY_AUTHORIZATION_URL_DEFAULT
    request_token_url = BSKY_PAR_URL_DEFAULT
    access_token_url = BSKY_TOKEN_URL_DEFAULT
    profile_url = BSKY_PUBLIC_PROFILE_URL_DEFAULT

    urls_customizable = True
    pkce = PKCEMethod.S256
    client_secret_required = False

    def icon_url(self) -> str:
        return static("authentik/sources/atproto.svg")

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("handle") or info.get("did"),
            "email": info.get("email"),
            "name": info.get("displayName") or info.get("handle"),
        }
