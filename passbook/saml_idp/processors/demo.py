"""
Demo Processor
"""

from supervisr.mod.auth.saml.idp.base import Processor
from supervisr.mod.auth.saml.idp.xml_render import get_assertion_xml


class DemoProcessor(Processor):
    """
    Demo Response Handler Processor for testing against django-saml2-sp.
    """

    def _format_assertion(self):
        # NOTE: This uses the SalesForce assertion for the demo.
        self._assertion_xml = get_assertion_xml(
            'saml/xml/assertions/salesforce.xml', self._assertion_params, signed=True)


class DemoAttributeProcessor(Processor):
    """
    Demo Response Handler Processor for testing against django-saml2-sp;
    Adds SAML attributes to the assertion.
    """

    def _format_assertion(self):
        # NOTE: This uses the SalesForce assertion for the demo.
        self._assertion_params['ATTRIBUTES'] = {
            'foo': 'bar',
        }
        self._assertion_xml = get_assertion_xml(
            'saml/xml/assertions/salesforce.xml', self._assertion_params, signed=True)
