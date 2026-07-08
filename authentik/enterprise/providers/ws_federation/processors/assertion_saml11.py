"""SAML 1.1 Assertion generator for WS-Federation"""

from types import GeneratorType

import xmlsec
from lxml.etree import Element, SubElement, _Element  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    DIGEST_ALGORITHM_TRANSLATION_MAP,
    NS_SIGNATURE,
    SIGN_ALGORITHM_TRANSFORM_MAP,
)
from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.events.models import Event, EventAction
from authentik.events.signals import get_login_event
from authentik.lib.xml import remove_xml_newlines
from authentik.providers.saml.models import SAMLPropertyMapping
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.sources.saml.exceptions import InvalidSignature
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD

LOGGER = get_logger()

# SAML 1.0 and 1.1 share this namespace; version is set via MajorVersion/MinorVersion attributes
NS_SAML11_ASSERTION = "urn:oasis:names:tc:SAML:1.0:assertion"
NS_MAP_SAML11 = {"saml": NS_SAML11_ASSERTION, "ds": NS_SIGNATURE}

SAML11_CM_BEARER = "urn:oasis:names:tc:SAML:1.0:cm:bearer"
SAML11_AM_PASSWORD = "urn:oasis:names:tc:SAML:1.0:am:password"
SAML11_AM_UNSPECIFIED = "urn:oasis:names:tc:SAML:1.0:am:unspecified"
WSFED_ATTRIBUTE_NAMESPACE = "http://schemas.xmlsoap.org/claims"


class SAML11AssertionProcessor(AssertionProcessor):
    """SAML 1.1 assertion builder, overriding the SAML 2.0 methods that differ."""

    def get_name_id(self) -> _Element:
        # same value/format resolution as SAML 2.0, wrapped as NameIdentifier instead of NameID
        name_id = super().get_name_id()
        name_identifier = Element(f"{{{NS_SAML11_ASSERTION}}}NameIdentifier")
        name_identifier.attrib["Format"] = name_id.attrib["Format"]
        name_identifier.text = name_id.text
        return name_identifier

    def get_assertion_subject(self) -> _Element:
        # SAML 1.1 has no assertion-level Subject; each statement embeds its own
        subject = Element(f"{{{NS_SAML11_ASSERTION}}}Subject")
        subject.append(self.get_name_id())

        subject_confirmation = SubElement(subject, f"{{{NS_SAML11_ASSERTION}}}SubjectConfirmation")
        confirmation_method = SubElement(
            subject_confirmation, f"{{{NS_SAML11_ASSERTION}}}ConfirmationMethod"
        )
        confirmation_method.text = SAML11_CM_BEARER
        return subject

    def get_assertion_conditions(self) -> _Element:
        conditions = Element(f"{{{NS_SAML11_ASSERTION}}}Conditions")
        conditions.attrib["NotBefore"] = self._valid_not_before
        conditions.attrib["NotOnOrAfter"] = self._valid_not_on_or_after
        if self.provider.audience != "":
            audience_restriction_condition = SubElement(
                conditions, f"{{{NS_SAML11_ASSERTION}}}AudienceRestrictionCondition"
            )
            audience = SubElement(
                audience_restriction_condition, f"{{{NS_SAML11_ASSERTION}}}Audience"
            )
            audience.text = self.provider.audience
        return conditions

    def get_assertion_auth_n_statement(self) -> _Element:
        auth_statement = Element(f"{{{NS_SAML11_ASSERTION}}}AuthenticationStatement")
        auth_statement.attrib["AuthenticationInstant"] = self._auth_instant
        auth_statement.attrib["AuthenticationMethod"] = SAML11_AM_UNSPECIFIED

        event = get_login_event(self.http_request)
        if event and event.context.get(PLAN_CONTEXT_METHOD, "") == "password":
            auth_statement.attrib["AuthenticationMethod"] = SAML11_AM_PASSWORD

        if self.provider.authn_context_class_ref_mapping:
            try:
                value = self.provider.authn_context_class_ref_mapping.evaluate(
                    user=self.http_request.user,
                    request=self.http_request,
                    provider=self.provider,
                )
                if value is not None:
                    auth_statement.attrib["AuthenticationMethod"] = str(value)
            except PropertyMappingExpressionException as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        "Failed to evaluate property-mapping: "
                        f"'{self.provider.authn_context_class_ref_mapping.name}'"
                    ),
                    provider=self.provider,
                    mapping=self.provider.authn_context_class_ref_mapping,
                ).from_http(self.http_request)
                LOGGER.warning("Failed to evaluate property mapping", exc=exc)

        auth_statement.append(self.get_assertion_subject())
        return auth_statement

    def get_attributes(self) -> _Element | None:
        # None if empty: SAML 1.1's schema requires at least one Attribute per AttributeStatement
        attribute_statement = Element(f"{{{NS_SAML11_ASSERTION}}}AttributeStatement")
        attribute_statement.append(self.get_assertion_subject())
        user = self.http_request.user
        has_attribute = False
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

                attribute = Element(f"{{{NS_SAML11_ASSERTION}}}Attribute")
                attribute.attrib["AttributeName"] = mapping.saml_name
                attribute.attrib["AttributeNamespace"] = WSFED_ATTRIBUTE_NAMESPACE

                if not isinstance(value, list | GeneratorType):
                    value = [value]

                for value_item in value:
                    attribute_value = SubElement(
                        attribute, f"{{{NS_SAML11_ASSERTION}}}AttributeValue"
                    )
                    str_value = str(value_item) if not isinstance(value_item, str) else value_item
                    attribute_value.text = str_value

                attribute_statement.append(attribute)
                has_attribute = True
            except (PropertyMappingExpressionException, ValueError) as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping: '{mapping.name}'",
                    provider=self.provider,
                    mapping=mapping,
                ).from_http(self.http_request)
                LOGGER.warning("Failed to evaluate property mapping", exc=exc)
                continue
        if not has_attribute:
            return None
        return attribute_statement

    def get_assertion(self) -> _Element:
        assertion = Element(f"{{{NS_SAML11_ASSERTION}}}Assertion", nsmap=NS_MAP_SAML11)
        assertion.attrib["MajorVersion"] = "1"
        assertion.attrib["MinorVersion"] = "1"
        assertion.attrib["AssertionID"] = self._assertion_id
        assertion.attrib["IssueInstant"] = self._issue_instant
        self.issuer = self._get_issuer_value()
        assertion.attrib["Issuer"] = self.issuer

        assertion.append(self.get_assertion_conditions())
        assertion.append(self.get_assertion_auth_n_statement())
        attribute_statement = self.get_attributes()
        if attribute_statement is not None:
            assertion.append(attribute_statement)

        # unlike SAML 2.0, ds:Signature must be the last child of Assertion
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

        return assertion

    def _sign(self, element: _Element):
        # same as AssertionProcessor._sign, but referencing AssertionID instead of ID
        digest_algorithm_transform = DIGEST_ALGORITHM_TRANSLATION_MAP.get(
            self.provider.digest_algorithm, xmlsec.constants.TransformSha1
        )
        xmlsec.tree.add_ids(element, ["AssertionID"])
        signature_node = xmlsec.tree.find_node(element, xmlsec.constants.NodeSignature)
        ref = xmlsec.template.add_reference(
            signature_node,
            digest_algorithm_transform,
            uri="#" + element.attrib["AssertionID"],
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
            ctx.sign(remove_xml_newlines(element, signature_node))
        except xmlsec.Error as exc:
            raise InvalidSignature() from exc
