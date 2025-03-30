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
from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_WINDOWS,
    SAML_NAME_ID_FORMAT_X509,
)
from authentik.common.saml.exceptions import (
    InvalidEncryption,
    InvalidSignature,
    MismatchedRequestID,
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from authentik.core.models import (
    USER_ATTRIBUTE_DELETE_ON_LOGOUT,
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    USER_ATTRIBUTE_SOURCES,
    User,
)
from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.lib.utils.time import timedelta_from_string
from authentik.sources.saml.models import (
    GroupSAMLSourceConnection,
    SAMLSource,
    UserSAMLSourceConnection,
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

        if self._source.encryption_kp:
            self._decrypt_response()

        if self._source.verification_kp:
            self._verify_signed()
        self._verify_request_id()
        self._verify_status()

    def _decrypt_response(self):
        """Decrypt SAMLResponse EncryptedAssertion Element"""
        manager = xmlsec.KeysManager()
        key = xmlsec.Key.from_memory(
            self._source.encryption_kp.key_data,
            xmlsec.constants.KeyDataFormatPem,
        )

        manager.add_key(key)
        encryption_context = xmlsec.EncryptionContext(manager)

        encrypted_assertion = self._root.find(f".//{{{NS_SAML_ASSERTION}}}EncryptedAssertion")
        if encrypted_assertion is None:
            raise InvalidEncryption()
        encrypted_data = xmlsec.tree.find_child(
            encrypted_assertion, "EncryptedData", xmlsec.constants.EncNs
        )
        try:
            decrypted_assertion = encryption_context.decrypt(encrypted_data)
        except xmlsec.Error as exc:
            raise InvalidEncryption() from exc

        index_of = self._root.index(encrypted_assertion)
        self._root.remove(encrypted_assertion)
        self._root.insert(
            index_of,
            decrypted_assertion,
        )

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
        except xmlsec.Error as exc:
            raise InvalidSignature() from exc
        LOGGER.debug("Successfully verified signature")

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
        name_id = self._get_name_id()
        expiry = mktime(
            (now() + timedelta_from_string(self._source.temporary_user_delete_after)).timetuple()
        )
        user: User = User.objects.create(
            username=name_id.text,
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
        LOGGER.debug("Created temporary user for NameID Transient", username=name_id.text)
        user.set_unusable_password()
        user.save()
        UserSAMLSourceConnection.objects.create(
            source=self._source, user=user, identifier=name_id.text
        )
        return SAMLSourceFlowManager(
            source=self._source,
            request=self._http_request,
            identifier=str(name_id.text),
            user_info={
                "root": self._root,
                "name_id": name_id,
            },
            policy_context={},
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
            source=self._source,
            request=self._http_request,
            identifier=str(name_id.text),
            user_info={
                "root": self._root,
                "name_id": name_id,
            },
            policy_context={
                "saml_response": etree.tostring(self._root),
            },
        )


class SAMLSourceFlowManager(SourceFlowManager):
    """Source flow manager for SAML Sources"""

    user_connection_type = UserSAMLSourceConnection
    group_connection_type = GroupSAMLSourceConnection
