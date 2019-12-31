"""Salesforce Processor"""

from passbook.providers.saml.base import Processor
from passbook.providers.saml.xml_render import get_assertion_xml


class SalesForceProcessor(Processor):
    """SalesForce.com-specific SAML 2.0 AuthnRequest to Response Handler Processor."""

    def _determine_audience(self):
        self._audience = "IAMShowcase"

    def _format_assertion(self):
        self._assertion_xml = get_assertion_xml(
            "saml/xml/assertions/salesforce.xml", self._assertion_params, signed=True
        )
