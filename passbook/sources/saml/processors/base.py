"""passbook saml source processor"""
from typing import Optional
from xml.etree.ElementTree import Element

from defusedxml import ElementTree
from django.http import HttpRequest
from signxml import XMLVerifier
from structlog import get_logger

from passbook.core.models import User
from passbook.providers.saml.utils.encoding import decode_base64_and_inflate
from passbook.sources.saml.exceptions import (
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from passbook.sources.saml.models import SAMLSource

LOGGER = get_logger()


class Processor:
    """SAML Response Processor"""

    _source: SAMLSource

    _root: Element
    _root_xml: str

    def __init__(self, source: SAMLSource):
        self._source = source

    def parse(self, request: HttpRequest):
        """Check if `request` contains SAML Response data, parse and validate it."""
        # First off, check if we have any SAML Data at all.
        raw_response = request.POST.get("SAMLResponse", None)
        if not raw_response:
            raise MissingSAMLResponse("Request does not contain 'SAMLResponse'")
        # relay_state = request.POST.get('RelayState', None)
        # Check if response is compressed, b64 decode it
        self._root_xml = decode_base64_and_inflate(raw_response)
        self._root = ElementTree.fromstring(self._root_xml)
        # Verify signed XML
        self._verify_signed()

    def _verify_signed(self):
        """Verify SAML Response's Signature"""
        verifier = XMLVerifier()
        verifier.verify(self._root_xml, x509_cert=self._source.signing_cert)

    def _get_email(self) -> Optional[str]:
        """
        Returns the email out of the response.

        At present, response must pass the email address as the Subject, eg.:

        <saml:Subject>
                <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                            SPNameQualifier=""
                            >email@example.com</saml:NameID>
        """
        assertion = self._root.find("{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")
        subject = assertion.find("{urn:oasis:names:tc:SAML:2.0:assertion}Subject")
        name_id = subject.find("{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
        name_id_format = name_id.attrib["Format"]
        if name_id_format != "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress":
            raise UnsupportedNameIDFormat(
                f"Assertion contains NameID with unsupported format {name_id_format}."
            )
        return name_id.text

    def get_user(self) -> User:
        """
        Gets info out of the response and locally logs in this user.
        May create a local user account first.
        Returns the user object that was created.
        """
        email = self._get_email()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(username=email, email=email)
            # TODO: Property Mappings
            user.set_unusable_password()
            user.save()
        return user
