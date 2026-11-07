"""SAML AuthNRequest Parser and dataclass"""

from base64 import b64decode
from dataclasses import dataclass
from xml.etree.ElementTree import ParseError  # nosec

from defusedxml import ElementTree
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    NS_SAML_PROTOCOL,
    SAML_NAME_ID_FORMAT_UNSPECIFIED,
)
from authentik.common.saml.exceptions import ERROR_CANNOT_DECODE_REQUEST, CannotHandleAssertion
from authentik.common.saml.parsers.verify import (
    verify_detached_signature,
    verify_enveloped_signature,
)
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate
from authentik.sources.saml.models import SAMLNameIDPolicy


@dataclass(slots=True)
class AuthNRequest:
    """AuthNRequest Dataclass"""

    id: str | None = None

    relay_state: str | None = None

    name_id_policy: str = SAML_NAME_ID_FORMAT_UNSPECIFIED

    force_authn: bool = False

    # The ACS URL the response is sent to, resolved from the request and validated against the
    # provider's configured ACS URLs. When unset, the provider's default ACS URL is used.
    acs_url: str | None = None


def get_acs_url(provider: SAMLProvider, auth_n_request: AuthNRequest) -> str:
    """Get the URL a response for `auth_n_request` should be sent to"""
    # Requests parsed before `acs_url` existed might be stored in a flow plan,
    # where the slot is missing, so don't assume it's set.
    return getattr(auth_n_request, "acs_url", None) or provider.acs_url


class AuthNRequestParser:
    """AuthNRequest Parser"""

    provider: SAMLProvider

    def __init__(self, provider: SAMLProvider):
        self.provider = provider
        self.logger = get_logger().bind(provider=self.provider)

    def _parse_xml(self, decoded_xml: str | bytes, relay_state: str | None) -> AuthNRequest:
        try:
            root = ElementTree.fromstring(decoded_xml)
        except (ParseError, ValueError) as exc:
            self.logger.warning("Failed to parse SAML request", exc=exc)
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST) from exc
        # `ID` is a required attribute of every SAML request (SAML 2.0 core §3.2.1)
        if "ID" not in root.attrib:
            self.logger.warning("SAML request is missing the ID attribute")
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST)

        acs_url = self._resolve_acs_url(root)

        # `ForceAuthn` is an optional attribute. When true, the SP requires the IdP to
        # actively re-authenticate the user instead of relying on an existing session
        # (SAML 2.0 core §3.4.1).
        force_authn = root.attrib.get("ForceAuthn", "false").lower() == "true"

        auth_n_request = AuthNRequest(
            id=root.attrib["ID"],
            relay_state=relay_state,
            force_authn=force_authn,
            acs_url=acs_url,
        )

        # Check if AuthnRequest has a NameID Policy object
        name_id_policies = root.findall(f"{{{NS_SAML_PROTOCOL}}}NameIDPolicy")
        if len(name_id_policies) > 0:
            name_id_policy = name_id_policies[0]
            auth_n_request.name_id_policy = name_id_policy.attrib.get(
                "Format", SAML_NAME_ID_FORMAT_UNSPECIFIED
            )

        return auth_n_request

    def _resolve_acs_url(self, root) -> str:
        """Resolve the URL to send the response to, and make sure it's configured for the provider.

        `AssertionConsumerServiceURL` and `AssertionConsumerServiceIndex` are optional and
        mutually exclusive. When neither is set, the default ACS URL is used
        (SAML 2.0 core 3.4.1 http://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf)
        """
        request_acs_url = root.attrib.get("AssertionConsumerServiceURL")
        request_acs_index = root.attrib.get("AssertionConsumerServiceIndex")
        if request_acs_url is not None and request_acs_index is not None:
            self.logger.warning(
                "SAML request specifies both AssertionConsumerServiceURL and "
                "AssertionConsumerServiceIndex"
            )
            raise CannotHandleAssertion(
                "AssertionConsumerServiceURL and AssertionConsumerServiceIndex are mutually "
                "exclusive."
            )
        index = None
        if request_acs_index is not None:
            try:
                index = int(request_acs_index)
            except ValueError:
                raise CannotHandleAssertion(
                    f"Invalid AssertionConsumerServiceIndex {request_acs_index}."
                ) from None
        acs_url = self.provider.resolve_acs_url(url=request_acs_url, index=index)
        if acs_url:
            return acs_url
        if request_acs_url is not None:
            self.logger.warning(
                "ACS URL of request doesn't match any provider ACS URL",
                request_acs_url=request_acs_url,
            )
            raise CannotHandleAssertion(
                f"ACS URL of {request_acs_url} doesn't match any ACS URL configured for the "
                "provider."
            )
        if index is not None:
            self.logger.warning(
                "ACS index of request doesn't match any provider ACS URL", request_acs_index=index
            )
            raise CannotHandleAssertion(
                f"ACS index {index} doesn't match any ACS URL configured for the provider."
            )
        self.logger.warning("Provider has no default ACS URL")
        raise CannotHandleAssertion("Provider has no default ACS URL configured.")

    def parse(self, saml_request: str, relay_state: str | None = None) -> AuthNRequest:
        """Validate and parse raw request with enveloped signautre."""
        try:
            decoded_xml = b64decode(saml_request.encode())
        except ValueError as exc:
            self.logger.warning("Failed to decode SAML request", exc=exc)
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST) from exc

        verifier = self.provider.verification_kp
        if not verifier:
            return self._parse_xml(decoded_xml, relay_state)

        verify_enveloped_signature(decoded_xml, verifier, "/samlp:AuthnRequest/ds:Signature")

        return self._parse_xml(decoded_xml, relay_state)

    def parse_detached(
        self,
        saml_request: str,
        relay_state: str | None,
        signature: str | None = None,
        sig_alg: str | None = None,
    ) -> AuthNRequest:
        """Validate and parse raw request with detached signature"""
        try:
            decoded_xml = decode_base64_and_inflate(saml_request)
        except ValueError as exc:
            self.logger.warning("Failed to decode SAML request", exc=exc)
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST) from exc

        verifier = self.provider.verification_kp
        if not verifier:
            return self._parse_xml(decoded_xml, relay_state)

        verify_detached_signature(
            "SAMLRequest", saml_request, relay_state, signature, sig_alg, verifier
        )
        return self._parse_xml(decoded_xml, relay_state)

    def idp_initiated(self) -> AuthNRequest:
        """Create IdP Initiated AuthNRequest"""
        request = AuthNRequest(relay_state=None)
        if self.provider.default_relay_state != "":
            request.relay_state = self.provider.default_relay_state
        if self.provider.default_name_id_policy != SAMLNameIDPolicy.UNSPECIFIED:
            request.name_id_policy = self.provider.default_name_id_policy
        return request
