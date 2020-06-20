"""Salesforce Processor"""

from passbook.providers.saml.processors.generic import GenericProcessor
from passbook.providers.saml.utils.xml_render import get_assertion_xml


class SalesForceProcessor(GenericProcessor):
    """SalesForce.com-specific SAML 2.0 AuthnRequest to Response Handler Processor."""

    def _format_assertion(self):
        super()._format_assertion()
        self._assertion_xml = get_assertion_xml(
            "providers/saml/xml/assertions/salesforce.xml",
            self._assertion_params,
            signed=True,
        )
