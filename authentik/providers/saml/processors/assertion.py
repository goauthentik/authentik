"""SAML Assertion generator"""

from datetime import datetime
from hashlib import sha256
from types import GeneratorType

import xmlsec
from django.http import HttpRequest
from lxml import etree  # nosec
from lxml.etree import Element, SubElement  # nosec
from structlog.stdlib import get_logger

from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.events.models import Event, EventAction
from authentik.events.signals import get_login_event
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.authn_request_parser import AuthNRequest
from authentik.providers.saml.utils import get_random_id
from authentik.providers.saml.utils.time import get_time_string
from authentik.sources.ldap.auth import LDAP_DISTINGUISHED_NAME
from authentik.sources.saml.exceptions import (
    InvalidEncryption,
    InvalidSignature,
    UnsupportedNameIDFormat,
)
from authentik.sources.saml.processors.constants import (
    DIGEST_ALGORITHM_TRANSLATION_MAP,
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_UNSPECIFIED,
    SAML_NAME_ID_FORMAT_WINDOWS,
    SAML_NAME_ID_FORMAT_X509,
    SIGN_ALGORITHM_TRANSFORM_MAP,
)
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

LOGGER = get_logger()


class AssertionProcessor:
    """Generate a SAML Response from an AuthNRequest"""

    provider: SAMLProvider
    http_request: HttpRequest
    auth_n_request: AuthNRequest

    _issue_instant: str
    _assertion_id: str
    _response_id: str

    _auth_instant: str
    _valid_not_before: str
    _session_not_on_or_after: str
    _valid_not_on_or_after: str

    def __init__(self, provider: SAMLProvider, request: HttpRequest, auth_n_request: AuthNRequest):
        self.provider = provider
        self.http_request = request
        self.auth_n_request = auth_n_request

        self._issue_instant = get_time_string()
        self._assertion_id = get_random_id()
        self._response_id = get_random_id()

        _login_event = get_login_event(self.http_request)
        _login_time = datetime.now()
        if _login_event:
            _login_time = _login_event.created
        self._auth_instant = get_time_string(_login_time)
        self._valid_not_before = get_time_string(
            timedelta_from_string(self.provider.assertion_valid_not_before)
        )
        self._session_not_on_or_after = get_time_string(
            timedelta_from_string(self.provider.session_valid_not_on_or_after)
        )
        self._valid_not_on_or_after = get_time_string(
            timedelta_from_string(self.provider.assertion_valid_not_on_or_after)
        )

    def get_attributes(self) -> Element:
        """Get AttributeStatement Element with Attributes from Property Mappings."""
        # https://commons.lbl.gov/display/IDMgmt/Attribute+Definitions
        attribute_statement = Element(f"{{{NS_SAML_ASSERTION}}}AttributeStatement")
        user = self.http_request.user
        for mapping in SAMLPropertyMapping.objects.filter(provider=self.provider).order_by(
            "saml_name"
        ):
            try:
                mapping: SAMLPropertyMapping
                value = mapping.evaluate(
                    user=user,
                    request=self.http_request,
                    provider=self.provider,
                )
                if value is None:
                    continue

                attribute = Element(f"{{{NS_SAML_ASSERTION}}}Attribute")
                if mapping.friendly_name and mapping.friendly_name != "":
                    attribute.attrib["FriendlyName"] = mapping.friendly_name
                attribute.attrib["Name"] = mapping.saml_name

                if not isinstance(value, list | GeneratorType):
                    value = [value]

                for value_item in value:
                    attribute_value = SubElement(
                        attribute, f"{{{NS_SAML_ASSERTION}}}AttributeValue"
                    )
                    str_value = str(value_item) if not isinstance(value_item, str) else value_item
                    attribute_value.text = str_value

                attribute_statement.append(attribute)

            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping: '{mapping.name}'",
                    provider=self.provider,
                    mapping=mapping,
                ).from_http(self.http_request)
                LOGGER.warning("Failed to evaluate property mapping", exc=exc)
                continue
        return attribute_statement

    def get_issuer(self) -> Element:
        """Get Issuer Element"""
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer", nsmap=NS_MAP)
        issuer.text = self.provider.issuer
        return issuer

    def get_assertion_auth_n_statement(self) -> Element:
        """Generate AuthnStatement with AuthnContext and ContextClassRef Elements."""
        auth_n_statement = Element(f"{{{NS_SAML_ASSERTION}}}AuthnStatement")
        auth_n_statement.attrib["AuthnInstant"] = self._auth_instant
        auth_n_statement.attrib["SessionIndex"] = sha256(
            self.http_request.session.session_key.encode("ascii")
        ).hexdigest()
        auth_n_statement.attrib["SessionNotOnOrAfter"] = self._session_not_on_or_after

        auth_n_context = SubElement(auth_n_statement, f"{{{NS_SAML_ASSERTION}}}AuthnContext")
        auth_n_context_class_ref = SubElement(
            auth_n_context, f"{{{NS_SAML_ASSERTION}}}AuthnContextClassRef"
        )
        auth_n_context_class_ref.text = "urn:oasis:names:tc:SAML:2.0:ac:classes:unspecified"
        event = get_login_event(self.http_request)
        if event:
            method = event.context.get(PLAN_CONTEXT_METHOD, "")
            method_args = event.context.get(PLAN_CONTEXT_METHOD_ARGS, {})
            if method == "password":
                auth_n_context_class_ref.text = (
                    "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"
                )
            if "mfa_devices" in method_args:
                auth_n_context_class_ref.text = (
                    "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract"
                )
            if method in ["auth_mfa", "auth_webauthn_pwl"]:
                auth_n_context_class_ref.text = (
                    "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileOneFactorContract"
                )
        if self.provider.authn_context_class_ref_mapping:
            try:
                value = self.provider.authn_context_class_ref_mapping.evaluate(
                    user=self.http_request.user,
                    request=self.http_request,
                    provider=self.provider,
                )
                if value is not None:
                    auth_n_context_class_ref.text = str(value)
                return auth_n_statement
            except PropertyMappingExpressionException as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        "Failed to evaluate property-mapping: "
                        f"'{self.provider.authn_context_class_ref_mapping.name}'",
                    ),
                    provider=self.provider,
                    mapping=self.provider.authn_context_class_ref_mapping,
                ).from_http(self.http_request)
                LOGGER.warning("Failed to evaluate property mapping", exc=exc)
                return auth_n_statement
        return auth_n_statement

    def get_assertion_conditions(self) -> Element:
        """Generate Conditions with AudienceRestriction and Audience Elements."""
        conditions = Element(f"{{{NS_SAML_ASSERTION}}}Conditions")
        conditions.attrib["NotBefore"] = self._valid_not_before
        conditions.attrib["NotOnOrAfter"] = self._valid_not_on_or_after
        if self.provider.audience != "":
            audience_restriction = SubElement(
                conditions, f"{{{NS_SAML_ASSERTION}}}AudienceRestriction"
            )
            audience = SubElement(audience_restriction, f"{{{NS_SAML_ASSERTION}}}Audience")
            audience.text = self.provider.audience
        return conditions

    def get_name_id(self) -> Element:
        """Get NameID Element"""
        name_id = Element(f"{{{NS_SAML_ASSERTION}}}NameID")
        name_id.attrib["Format"] = self.auth_n_request.name_id_policy
        # persistent is used as a fallback, so always generate it
        persistent = self.http_request.user.uid
        name_id.text = persistent
        # If name_id_mapping is set, we override the value, regardless of what the SP asks for
        if self.provider.name_id_mapping:
            try:
                value = self.provider.name_id_mapping.evaluate(
                    user=self.http_request.user,
                    request=self.http_request,
                    provider=self.provider,
                )
                if value is not None:
                    name_id.text = str(value)
                return name_id
            except PropertyMappingExpressionException as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        "Failed to evaluate property-mapping: "
                        f"'{self.provider.name_id_mapping.name}'",
                    ),
                    provider=self.provider,
                    mapping=self.provider.name_id_mapping,
                ).from_http(self.http_request)
                LOGGER.warning("Failed to evaluate property mapping", exc=exc)
                return name_id
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_EMAIL:
            name_id.text = self.http_request.user.email
            return name_id
        if name_id.attrib["Format"] in [
            SAML_NAME_ID_FORMAT_PERSISTENT,
            SAML_NAME_ID_FORMAT_UNSPECIFIED,
        ]:
            name_id.text = persistent
            return name_id
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_X509:
            # This attribute is statically set by the LDAP source
            name_id.text = self.http_request.user.attributes.get(
                LDAP_DISTINGUISHED_NAME, persistent
            )
            return name_id
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_WINDOWS:
            # This attribute is statically set by the LDAP source
            name_id.text = self.http_request.user.attributes.get("upn", persistent)
            return name_id
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_TRANSIENT:
            # Use the hash of the user's session, which changes every session
            session_key: str = self.http_request.session.session_key
            name_id.text = sha256(session_key.encode()).hexdigest()
            return name_id
        raise UnsupportedNameIDFormat(
            f"Assertion contains NameID with unsupported format {name_id.attrib['Format']}."
        )

    def get_assertion_subject(self) -> Element:
        """Generate Subject Element with NameID and SubjectConfirmation Objects"""
        subject = Element(f"{{{NS_SAML_ASSERTION}}}Subject")
        subject.append(self.get_name_id())

        subject_confirmation = SubElement(subject, f"{{{NS_SAML_ASSERTION}}}SubjectConfirmation")
        subject_confirmation.attrib["Method"] = "urn:oasis:names:tc:SAML:2.0:cm:bearer"

        subject_confirmation_data = SubElement(
            subject_confirmation, f"{{{NS_SAML_ASSERTION}}}SubjectConfirmationData"
        )
        if self.auth_n_request.id:
            subject_confirmation_data.attrib["InResponseTo"] = self.auth_n_request.id
        subject_confirmation_data.attrib["NotOnOrAfter"] = self._valid_not_on_or_after
        subject_confirmation_data.attrib["Recipient"] = self.provider.acs_url
        return subject

    def get_assertion(self) -> Element:
        """Generate Main Assertion Element"""
        assertion = Element(f"{{{NS_SAML_ASSERTION}}}Assertion", nsmap=NS_MAP)
        assertion.attrib["Version"] = "2.0"
        assertion.attrib["ID"] = self._assertion_id
        assertion.attrib["IssueInstant"] = self._issue_instant
        assertion.append(self.get_issuer())

        if self.provider.signing_kp and self.provider.sign_assertion:
            sign_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
                self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha1
            )
            signature = xmlsec.template.create(
                assertion,
                xmlsec.constants.TransformExclC14N,
                sign_algorithm_transform,
                ns=xmlsec.constants.DSigNs,
            )
            assertion.append(signature)
        if self.provider.encryption_kp:
            encryption = xmlsec.template.encrypted_data_create(
                assertion,
                xmlsec.constants.TransformAes128Cbc,
                self._assertion_id,
                ns=xmlsec.constants.DSigNs,
            )
            assertion.append(encryption)

        assertion.append(self.get_assertion_subject())
        assertion.append(self.get_assertion_conditions())
        assertion.append(self.get_assertion_auth_n_statement())

        assertion.append(self.get_attributes())
        return assertion

    def get_response(self) -> Element:
        """Generate Root response element"""
        response = Element(f"{{{NS_SAML_PROTOCOL}}}Response", nsmap=NS_MAP)
        response.attrib["Version"] = "2.0"
        response.attrib["IssueInstant"] = self._issue_instant
        response.attrib["Destination"] = self.provider.acs_url
        response.attrib["ID"] = self._response_id
        if self.auth_n_request.id:
            response.attrib["InResponseTo"] = self.auth_n_request.id

        response.append(self.get_issuer())

        if self.provider.signing_kp and self.provider.sign_response:
            sign_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
                self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha1
            )
            signature = xmlsec.template.create(
                response,
                xmlsec.constants.TransformExclC14N,
                sign_algorithm_transform,
                ns=xmlsec.constants.DSigNs,
            )
            response.append(signature)

        status = SubElement(response, f"{{{NS_SAML_PROTOCOL}}}Status")
        status_code = SubElement(status, f"{{{NS_SAML_PROTOCOL}}}StatusCode")
        status_code.attrib["Value"] = "urn:oasis:names:tc:SAML:2.0:status:Success"

        response.append(self.get_assertion())
        return response

    def _sign(self, element: Element):
        """Sign an XML element based on the providers' configured signing settings"""
        digest_algorithm_transform = DIGEST_ALGORITHM_TRANSLATION_MAP.get(
            self.provider.digest_algorithm, xmlsec.constants.TransformSha1
        )
        xmlsec.tree.add_ids(element, ["ID"])
        signature_node = xmlsec.tree.find_node(element, xmlsec.constants.NodeSignature)
        ref = xmlsec.template.add_reference(
            signature_node,
            digest_algorithm_transform,
            uri="#" + element.attrib["ID"],
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)
        key_info = xmlsec.template.ensure_key_info(signature_node)
        xmlsec.template.add_x509_data(key_info)

        ctx = xmlsec.SignatureContext()

        key = xmlsec.Key.from_memory(
            self.provider.signing_kp.key_data,
            xmlsec.constants.KeyDataFormatPem,
            None,
        )
        key.load_cert_from_memory(
            self.provider.signing_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
        )
        ctx.key = key
        try:
            ctx.sign(signature_node)
        except xmlsec.Error as exc:
            raise InvalidSignature() from exc

    def _encrypt(self, element: Element, parent: Element):
        """Encrypt SAMLResponse EncryptedAssertion Element"""
        manager = xmlsec.KeysManager()
        key = xmlsec.Key.from_memory(
            self.provider.encryption_kp.key_data,
            xmlsec.constants.KeyDataFormatPem,
        )
        key.load_cert_from_memory(
            self.provider.encryption_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
        )

        manager.add_key(key)
        encryption_context = xmlsec.EncryptionContext(manager)
        encryption_context.key = xmlsec.Key.generate(
            xmlsec.constants.KeyDataAes, 128, xmlsec.constants.KeyDataTypeSession
        )

        container = SubElement(parent, f"{{{NS_SAML_ASSERTION}}}EncryptedAssertion")
        enc_data = xmlsec.template.encrypted_data_create(
            container, xmlsec.Transform.AES128, type=xmlsec.EncryptionType.ELEMENT, ns="xenc"
        )
        xmlsec.template.encrypted_data_ensure_cipher_value(enc_data)
        key_info = xmlsec.template.encrypted_data_ensure_key_info(enc_data, ns="ds")
        enc_key = xmlsec.template.add_encrypted_key(key_info, xmlsec.Transform.RSA_OAEP)
        xmlsec.template.encrypted_data_ensure_cipher_value(enc_key)

        try:
            enc_data = encryption_context.encrypt_xml(enc_data, element)
        except xmlsec.Error as exc:
            raise InvalidEncryption() from exc

        parent.remove(enc_data)
        container.append(enc_data)

    def build_response(self) -> str:
        """Build string XML Response and sign if signing is enabled."""
        root_response = self.get_response()
        if self.provider.signing_kp:
            if self.provider.sign_assertion:
                assertion = root_response.xpath("//saml:Assertion", namespaces=NS_MAP)[0]
                self._sign(assertion)
            if self.provider.sign_response:
                response = root_response.xpath("//samlp:Response", namespaces=NS_MAP)[0]
                self._sign(response)
        if self.provider.encryption_kp:
            assertion = root_response.xpath("//saml:Assertion", namespaces=NS_MAP)[0]
            self._encrypt(assertion, root_response)
        return etree.tostring(root_response).decode("utf-8")  # nosec
