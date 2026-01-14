"""authentik saml source processor"""

from base64 import b64decode
from hashlib import sha256
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

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    USER_ATTRIBUTE_TRANSIENT_TOKEN,
    SourceUserMatchingModes,
)
from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.lib.utils.time import timedelta_from_string
from authentik.sources.saml.exceptions import (
    InvalidEncryption,
    InvalidSignature,
    MismatchedRequestID,
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from authentik.sources.saml.models import (
    GroupSAMLSourceConnection,
    SAMLSource,
    UserSAMLSourceConnection,
)
from authentik.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_ATTRIBUTES_EPPN,
    SAML_ATTRIBUTES_EPTID,
    SAML_ATTRIBUTES_GROUP,
    SAML_ATTRIBUTES_MAIL,
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
        signatures = []

        if self._source.signed_response:
            signature_nodes = self._root.xpath("/samlp:Response/ds:Signature", namespaces=NS_MAP)

            if len(signature_nodes) != 1:
                raise InvalidSignature("No Signature exists in the Response element.")
            signatures.extend(signature_nodes)

        if self._source.signed_assertion:
            signature_nodes = self._root.xpath(
                "/samlp:Response/saml:Assertion/ds:Signature", namespaces=NS_MAP
            )

            if len(signature_nodes) != 1:
                raise InvalidSignature("No Signature exists in the Assertion element.")
            signatures.extend(signature_nodes)

        if len(signatures) == 0:
            raise InvalidSignature()

        for signature_node in signatures:
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
        if not (name_id.text and name_id.text.strip()):
            raise ValueError("NameID is empty")
        return name_id

    def _get_name_id_filter(self) -> dict[str, str]:
        """Returns the subject's NameID as a Filter for the `User`"""
        name_id_el = self._get_name_id()
        name_id = name_id_el.text
        if not name_id:
            raise UnsupportedNameIDFormat("Subject's NameID is empty.")
        _format = name_id_el.attrib.get("Format")
        if not _format:
            raise UnsupportedNameIDFormat("Subject's NameID has no Format attribute.")
        if _format == SAML_NAME_ID_FORMAT_EMAIL:
            return {"email": name_id}
        if _format == SAML_NAME_ID_FORMAT_PERSISTENT:
            return {"username": name_id}
        if _format == SAML_NAME_ID_FORMAT_TRANSIENT:
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

    def get_user_properties(self) -> dict[str, Any]:
        properties = {}
        root = self._root
        assertion = root.find(f"{{{NS_SAML_ASSERTION}}}Assertion")
        if assertion is None:
            raise ValueError("Assertion element not found")
        attribute_statement = assertion.find(f"{{{NS_SAML_ASSERTION}}}AttributeStatement")
        if attribute_statement is None:
            return properties
        # Get all attributes and their values into sub-attributes dict
        for attribute in attribute_statement.iterchildren():
            key = attribute.attrib["Name"]
            properties.setdefault(key, [])
            for value in attribute.iterchildren():
                if value.text is not None:
                    properties[key].append(value.text)
        if SAML_ATTRIBUTES_GROUP in properties:
            properties["groups"] = properties[SAML_ATTRIBUTES_GROUP]
            del properties[SAML_ATTRIBUTES_GROUP]
        # Flatten all lists in the dict except group
        for key, value in properties.items():
            if key != "groups":
                properties[key] = BaseEvaluator.expr_flatten(value)

        # Try to convert from SAML attributes if matching mode requires it
        if self._source.user_matching_mode in [
            SourceUserMatchingModes.EMAIL_LINK,
            SourceUserMatchingModes.EMAIL_DENY,
        ]:
            for attr in SAML_ATTRIBUTES_MAIL:
                if attr in properties:
                    properties["email"] = properties[attr]
                    break
        elif self._source.user_matching_mode in [
            SourceUserMatchingModes.USERNAME_LINK,
            SourceUserMatchingModes.USERNAME_DENY,
        ]:
            for attr in tuple(SAML_ATTRIBUTES_EPPN) + tuple(SAML_ATTRIBUTES_EPTID):
                if attr in properties:
                    properties["username"] = properties[attr]
                    break
        return properties

    def get_transient_connection_id(self, properties: dict, default: str) -> tuple[str, str]:
        """Prepare attributes for transient NameID handling"""
        identifier = default
        key = None
        for name, attrs in {
            "eppn": SAML_ATTRIBUTES_EPPN,
            "eptid": SAML_ATTRIBUTES_EPTID,
            "mail": SAML_ATTRIBUTES_MAIL,
            #            "uid": SAML_ATTRIBUTES_UID,
        }.items():
            for attr in attrs:
                if attr not in properties:
                    continue
                identifier = properties[attr]
                if isinstance(identifier, str) and identifier.strip():
                    key = name
                    properties[name] = identifier
                    break
            if key:
                break
        if not key:
            # No ID attribute found, handle as transient NameID
            if "attributes" not in properties:
                properties["attributes"] = {}
            properties["attributes"][USER_ATTRIBUTE_TRANSIENT_TOKEN] = sha256(
                default.encode("utf-8")
            ).hexdigest()
            expiry = mktime(
                (
                    now() + timedelta_from_string(self._source.temporary_user_delete_after)
                ).timetuple()
            )
            properties["attributes"][USER_ATTRIBUTE_EXPIRES] = expiry
            properties["attributes"][USER_ATTRIBUTE_GENERATED] = True
        return (key, identifier)

    def prepare_flow_manager(self) -> SourceFlowManager:
        """Prepare flow plan depending on whether or not the user exists"""
        name_id = self._get_name_id()
        # Sanity check, show a warning if NameIDPolicy doesn't match what we go
        fmt = name_id.attrib.get("Format")
        if self._source.name_id_policy != fmt:
            LOGGER.warning(
                "NameID from IdP doesn't match our policy",
                expected=self._source.name_id_policy,
                got=fmt,
            )
        properties = self.get_user_properties()
        identifier = name_id.text

        if fmt == SAML_NAME_ID_FORMAT_TRANSIENT:
            key, identifier = self.get_transient_connection_id(properties, name_id.text)
            # Ensure friendly username
            if key and "username" not in properties:
                properties["username"] = properties[key]

        return SAMLSourceFlowManager(
            source=self._source,
            request=self._http_request,
            identifier=identifier,
            user_info={
                "root": self._root,
                "name_id": name_id,
                "info": properties,
            },
            policy_context={
                "saml_response": etree.tostring(self._root),
            },
        )


class SAMLSourceFlowManager(SourceFlowManager):
    """Source flow manager for SAML Sources"""

    user_connection_type = UserSAMLSourceConnection
    group_connection_type = GroupSAMLSourceConnection
