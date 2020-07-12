"""SAML Assertion generator"""
from hashlib import sha256
from types import GeneratorType

from django.http import HttpRequest
from lxml import etree  # nosec
from lxml.etree import Element, SubElement  # nosec
from signxml import XMLSigner, XMLVerifier
from structlog import get_logger

from passbook.core.exceptions import PropertyMappingExpressionException
from passbook.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from passbook.providers.saml.processors.request_parser import AuthNRequest
from passbook.providers.saml.utils import get_random_id
from passbook.providers.saml.utils.time import get_time_string, timedelta_from_string
from passbook.sources.saml.exceptions import UnsupportedNameIDFormat
from passbook.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    NS_SIGNATURE,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_X509,
)

LOGGER = get_logger()


class AssertionProcessor:
    """Generate a SAML Response from an AuthNRequest"""

    provider: SAMLProvider
    http_request: HttpRequest
    auth_n_request: AuthNRequest

    _issue_instant: str
    _assertion_id: str

    _valid_not_before: str
    _valid_not_on_or_after: str

    def __init__(
        self, provider: SAMLProvider, request: HttpRequest, auth_n_request: AuthNRequest
    ):
        self.provider = provider
        self.http_request = request
        self.auth_n_request = auth_n_request

        self._issue_instant = get_time_string()
        self._assertion_id = get_random_id()

        self._valid_not_before = get_time_string(
            timedelta_from_string(self.provider.assertion_valid_not_before)
        )
        self._valid_not_on_or_after = get_time_string(
            timedelta_from_string(self.provider.assertion_valid_not_on_or_after)
        )

    def get_attributes(self) -> Element:
        """Get AttributeStatement Element with Attributes from Property Mappings."""
        # https://commons.lbl.gov/display/IDMgmt/Attribute+Definitions
        attribute_statement = Element(f"{{{NS_SAML_ASSERTION}}}AttributeStatement")
        for mapping in self.provider.property_mappings.all().select_subclasses():
            if not isinstance(mapping, SAMLPropertyMapping):
                continue
            try:
                mapping: SAMLPropertyMapping
                value = mapping.evaluate(
                    user=self.http_request.user,
                    request=self.http_request,
                    provider=self.provider,
                )
                if value is None:
                    continue

                attribute = Element(f"{{{NS_SAML_ASSERTION}}}Attribute")
                attribute.attrib["FriendlyName"] = mapping.friendly_name
                attribute.attrib["Name"] = mapping.saml_name

                if not isinstance(value, (list, GeneratorType)):
                    value = [value]

                for value_item in value:
                    attribute_value = SubElement(
                        attribute, f"{{{NS_SAML_ASSERTION}}}AttributeValue"
                    )
                    if not isinstance(value_item, str):
                        value_item = str(value_item)
                    attribute_value.text = value_item

                attribute_statement.append(attribute)

            except PropertyMappingExpressionException as exc:
                LOGGER.warning(exc)
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
        auth_n_statement.attrib["AuthnInstant"] = self._valid_not_before
        auth_n_statement.attrib["SessionIndex"] = self._assertion_id

        auth_n_context = SubElement(
            auth_n_statement, f"{{{NS_SAML_ASSERTION}}}AuthnContext"
        )
        auth_n_context_class_ref = SubElement(
            auth_n_context, f"{{{NS_SAML_ASSERTION}}}AuthnContextClassRef"
        )
        auth_n_context_class_ref.text = (
            "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"
        )
        return auth_n_statement

    def get_assertion_conditions(self) -> Element:
        """Generate Conditions with AudienceRestriction and Audience Elements."""
        conditions = Element(f"{{{NS_SAML_ASSERTION}}}Conditions")
        conditions.attrib["NotBefore"] = self._valid_not_before
        conditions.attrib["NotOnOrAfter"] = self._valid_not_on_or_after
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
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_EMAIL:
            name_id.text = self.http_request.user.email
            return name_id
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_PERSISTENT:
            name_id.text = self.http_request.user.username
            return name_id
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_X509:
            # This attribute is statically set by the LDAP source
            name_id.text = self.http_request.user.attributes.get(
                "distinguishedName", ""
            )
            return name_id
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_TRANSIENT:
            # This attribute is statically set by the LDAP source
            session_key: str = self.http_request.user.session.session_key
            name_id.text = sha256(session_key.encode()).hexdigest()
            return name_id
        raise UnsupportedNameIDFormat(
            f"Assertion contains NameID with unsupported format {name_id.attrib['Format']}."
        )

    def get_assertion_subject(self) -> Element:
        """Generate Subject Element with NameID and SubjectConfirmation Objects"""
        subject = Element(f"{{{NS_SAML_ASSERTION}}}Subject")
        subject.append(self.get_name_id())

        subject_confirmation = SubElement(
            subject, f"{{{NS_SAML_ASSERTION}}}SubjectConfirmation"
        )
        subject_confirmation.attrib["Method"] = "urn:oasis:names:tc:SAML:2.0:cm:bearer"

        subject_confirmation_data = SubElement(
            subject_confirmation, f"{{{NS_SAML_ASSERTION}}}SubjectConfirmationData"
        )
        if self.auth_n_request.id:
            subject_confirmation_data.attrib["InResponseTo"] = self.auth_n_request.id
        subject_confirmation_data.attrib["NotOnOrAfter"] = self._issue_instant
        subject_confirmation_data.attrib["Recipient"] = self.provider.acs_url
        return subject

    def get_assertion(self) -> Element:
        """Generate Main Assertion Element"""
        assertion = Element(f"{{{NS_SAML_ASSERTION}}}Assertion", nsmap=NS_MAP)
        assertion.attrib["Version"] = "2.0"
        assertion.attrib["ID"] = self._assertion_id
        assertion.attrib["IssueInstant"] = self._issue_instant
        assertion.append(self.get_issuer())

        if self.provider.signing_kp:
            # We need a placeholder signature as SAML requires the signature to be between
            # Issuer and subject
            signature_placeholder = SubElement(
                assertion, f"{{{NS_SIGNATURE}}}Signature", nsmap=NS_MAP
            )
            signature_placeholder.attrib["Id"] = "placeholder"

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
        response.attrib["ID"] = get_random_id()
        if self.auth_n_request.id:
            response.attrib["InResponseTo"] = self.auth_n_request.id

        response.append(self.get_issuer())

        status = SubElement(response, f"{{{NS_SAML_PROTOCOL}}}Status")
        status_code = SubElement(status, f"{{{NS_SAML_PROTOCOL}}}StatusCode")
        status_code.attrib["Value"] = "urn:oasis:names:tc:SAML:2.0:status:Success"

        response.append(self.get_assertion())
        return response

    def build_response(self) -> str:
        """Build string XML Response and sign if signing is enabled."""
        root_response = self.get_response()
        if self.provider.signing_kp:
            signer = XMLSigner(
                c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
                signature_algorithm=self.provider.signature_algorithm,
                digest_algorithm=self.provider.digest_algorithm,
            )
            signed = signer.sign(
                root_response,
                key=self.provider.signing_kp.private_key,
                cert=[self.provider.signing_kp.certificate_data],
                reference_uri=self._assertion_id,
            )
            XMLVerifier().verify(
                signed, x509_cert=self.provider.signing_kp.certificate_data
            )
            return etree.tostring(signed).decode("utf-8")  # nosec
        return etree.tostring(root_response).decode("utf-8")  # nosec
