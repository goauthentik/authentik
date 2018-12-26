"""AWS Processor"""

from passbook.saml_idp.base import Processor, xml_render


class AWSProcessor(Processor):
    """AWS Response Handler Processor for testing against django-saml2-sp."""

    def _determine_audience(self):
        self._audience = 'urn:amazon:webservices'

    def _format_assertion(self):
        """Formats _assertion_params as _assertion_xml."""
        self._assertion_params['ATTRIBUTES'] = [
            {
                'Name': 'https://aws.amazon.com/SAML/Attributes/RoleSessionName',
                'Value': self._django_request.user.username,
            },
            {
                'Name': 'https://aws.amazon.com/SAML/Attributes/Role',
                # 'Value': 'arn:aws:iam::471432361072:saml-provider/passbook_dev,
                # arn:aws:iam::471432361072:role/saml_role'
            }
        ]
        self._assertion_xml = xml_render.get_assertion_xml(
            'saml/xml/assertions/generic.xml', self._assertion_params, signed=True)
