"""authentik saml source processor"""
from base64 import b64decode
from time import mktime
from typing import TYPE_CHECKING, Any

import xmlsec
from defusedxml.lxml import fromstring
from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest
from django.utils.timezone import now
from structlog.stdlib import get_logger

from authentik.core.models import (
    USER_ATTRIBUTE_DELETE_ON_LOGOUT,
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    USER_ATTRIBUTE_SOURCES,
    User,
)
from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.utils import delete_none_values
from authentik.sources.saml.exceptions import (
    InvalidSignature,
    MismatchedRequestID,
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from authentik.sources.saml.models import SAMLSource, UserSAMLSourceConnection
from authentik.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_WINDOWS,
    SAML_NAME_ID_FORMAT_X509,
)
from authentik.sources.saml.processors.request import SESSION_KEY_REQUEST_ID

LOGGER = get_logger()
if TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec

CACHE_SEEN_REQUEST_ID = "authentik_saml_seen_ids_%s"


class ResponseProcessor:
    """SAML Response Processor"""

    _source: SAMLSource

    _root: Any
    _root_xml: bytes

    _http_request: HttpRequest

    def __init__(self, source: SAMLSource, request: HttpRequest):
        self._source = source
        self._http_request = request

    def parse(self):
        """Check if `request` contains SAML Response data, parse and validate it."""
        # First off, check if we have any SAML Data at all.
        raw_response = self._http_request.POST.get("SAMLResponse", None)
        if not raw_response:
            raise MissingSAMLResponse("Request does not contain 'SAMLResponse'")
        # Check if response is compressed, b64 decode it
        self._root_xml = b64decode(raw_response.encode())
        self._root = fromstring(self._root_xml)

        if self._source.verification_kp:
            self._verify_signed()
        self._verify_request_id()
        self._verify_status()

    def _verify_signed(self):
        """Verify SAML Response's Signature"""
        signature_nodes = self._root.xpath(
            "/samlp:Response/saml:Assertion/ds:Signature", namespaces=NS_MAP
        )
        if len(signature_nodes) != 1:
            raise InvalidSignature()
        signature_node = signature_nodes[0]
        xmlsec.tree.add_ids(self._root, ["ID"])

        ctx = xmlsec.SignatureContext()
        key = xmlsec.Key.from_memory(
            self._source.verification_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
        )
        ctx.key = key

        ctx.set_enabled_key_data([xmlsec.constants.KeyDataX509])
        try:
            ctx.verify(signature_node)
        except (xmlsec.InternalError, xmlsec.VerificationError) as exc:
            raise InvalidSignature from exc
        LOGGER.debug("Successfully verified signautre")

    def _verify_request_id(self):
        if self._source.allow_idp_initiated:
            # If IdP-initiated SSO flows are enabled, we want to cache the Response ID
            # somewhat mitigate replay attacks
            seen_ids = cache.get(CACHE_SEEN_REQUEST_ID % self._source.pk, [])
            if self._root.attrib["ID"] in seen_ids:
                raise SuspiciousOperation("Replay attack detected")
            seen_ids.append(self._root.attrib["ID"])
            cache.set(CACHE_SEEN_REQUEST_ID % self._source.pk, seen_ids)
            return
        if (
            SESSION_KEY_REQUEST_ID not in self._http_request.session
            or "InResponseTo" not in self._root.attrib
        ):
            raise MismatchedRequestID(
                "Missing InResponseTo and IdP-initiated Logins are not allowed"
            )
        if self._http_request.session[SESSION_KEY_REQUEST_ID] != self._root.attrib["InResponseTo"]:
            raise MismatchedRequestID("Mismatched request ID")

    def _verify_status(self):
        """Check for SAML Status elements"""
        status = self._root.find(f"{{{NS_SAML_PROTOCOL}}}Status")
        if status is None:
            return
        message = status.find(f"{{{NS_SAML_PROTOCOL}}}StatusMessage")
        if message is not None:
            raise ValueError(message.text)

    def _handle_name_id_transient(self) -> SourceFlowManager:
        """Handle a NameID with the Format of Transient. This is a bit more complex than other
        formats, as we need to create a temporary User that is used in the session. This
        user has an attribute that refers to our Source for cleanup. The user is also deleted
        on logout and periodically."""
        # Create a temporary User
        name_id = self._get_name_id().text
        expiry = mktime(
            (now() + timedelta_from_string(self._source.temporary_user_delete_after)).timetuple()
        )
        user: User = User.objects.create(
            username=name_id,
            attributes={
                USER_ATTRIBUTE_GENERATED: True,
                USER_ATTRIBUTE_SOURCES: [
                    self._source.name,
                ],
                USER_ATTRIBUTE_DELETE_ON_LOGOUT: True,
                USER_ATTRIBUTE_EXPIRES: expiry,
            },
            path=self._source.get_user_path(),
        )
        LOGGER.debug("Created temporary user for NameID Transient", username=name_id)
        user.set_unusable_password()
        user.save()
        UserSAMLSourceConnection.objects.create(source=self._source, user=user, identifier=name_id)
        return SAMLSourceFlowManager(
            self._source,
            self._http_request,
            name_id,
            delete_none_values(self.get_attributes()),
        )

    def _get_name_id(self) -> "Element":
        """Get NameID Element"""
        assertion = self._root.find(f"{{{NS_SAML_ASSERTION}}}Assertion")
        if assertion is None:
            raise ValueError("Assertion element not found")
        subject = assertion.find(f"{{{NS_SAML_ASSERTION}}}Subject")
        if subject is None:
            raise ValueError("Subject element not found")
        name_id = subject.find(f"{{{NS_SAML_ASSERTION}}}NameID")
        if name_id is None:
            raise ValueError("NameID element not found")
        return name_id

    def _get_name_id_filter(self) -> dict[str, str]:
        """Returns the subject's NameID as a Filter for the `User`"""
        name_id_el = self._get_name_id()
        name_id = name_id_el.text
        if not name_id:
            raise UnsupportedNameIDFormat("Subject's NameID is empty.")
        _format = name_id_el.attrib["Format"]
        if _format == SAML_NAME_ID_FORMAT_EMAIL:
            return {"email": name_id}
        if _format == SAML_NAME_ID_FORMAT_PERSISTENT:
            return {"username": name_id}
        if _format == SAML_NAME_ID_FORMAT_X509:
            # This attribute is statically set by the LDAP source
            return {"attributes__distinguishedName": name_id}
        if _format == SAML_NAME_ID_FORMAT_WINDOWS:
            if "\\" in name_id:
                name_id = name_id.split("\\")[1]
            return {"username": name_id}
        raise UnsupportedNameIDFormat(
            f"Assertion contains NameID with unsupported format {_format}."
        )

    def get_attributes(self) -> dict[str, list[str] | str]:
        """Get all attributes sent"""
        attributes = {}
        assertion = self._root.find(f"{{{NS_SAML_ASSERTION}}}Assertion")
        if assertion is None:
            raise ValueError("Assertion element not found")
        attribute_statement = assertion.find(f"{{{NS_SAML_ASSERTION}}}AttributeStatement")
        if attribute_statement is None:
            raise ValueError("Attribute statement element not found")
        # Get all attributes and their values into a dict
        for attribute in attribute_statement.iterchildren():
            key = attribute.attrib["Name"]
            attributes.setdefault(key, [])
            for value in attribute.iterchildren():
                attributes[key].append(value.text)
        # Flatten all lists in the dict
        for key, value in attributes.items():
            attributes[key] = BaseEvaluator.expr_flatten(value)
        attributes["username"] = self._get_name_id().text
        return attributes

    def prepare_flow_manager(self) -> SourceFlowManager:
        """Prepare flow plan depending on whether or not the user exists"""
        name_id = self._get_name_id()
        # Sanity check, show a warning if NameIDPolicy doesn't match what we go
        if self._source.name_id_policy != name_id.attrib["Format"]:
            LOGGER.warning(
                "NameID from IdP doesn't match our policy",
                expected=self._source.name_id_policy,
                got=name_id.attrib["Format"],
            )
        # transient NameIDs are handled separately as they don't have to go through flows.
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_TRANSIENT:
            return self._handle_name_id_transient()

        return SAMLSourceFlowManager(
            self._source,
            self._http_request,
            name_id.text,
            delete_none_values(self.get_attributes()),
        )


class SAMLSourceFlowManager(SourceFlowManager):
    """Source flow manager for SAML Sources"""

    connection_type = UserSAMLSourceConnection
