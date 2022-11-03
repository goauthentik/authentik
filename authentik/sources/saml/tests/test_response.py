"""SAML Source tests"""
from base64 import b64encode

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import dummy_get_response
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.response import ResponseProcessor

RESPONSE_ERROR = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol" Destination="https://127.0.0.1:9443/source/saml/google/acs/" ID="_ee7a8865ac457e7b22cb4f16b39ceca9" IssueInstant="2022-10-14T13:52:04.479Z" Version="2.0">
    <saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">https://accounts.google.com/o/saml2?idpid=</saml2:Issuer>
    <saml2p:Status>
        <saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Requester">
            <saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:RequestDenied"></saml2p:StatusCode>
        </saml2p:StatusCode>
        <saml2p:StatusMessage>Invalid request, ACS Url in request http://localhost:9000/source/saml/google/acs/ doesn't match configured ACS Url https://127.0.0.1:9443/source/saml/google/acs/.</saml2p:StatusMessage>
    </saml2p:Status>
</saml2p:Response>
"""

RESPONSE_SUCCESS = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol" Destination="https://127.0.0.1:9443/source/saml/google/acs/" ID="_1e17063957f10819a5a8e147971fec22" InResponseTo="_157fb504b59f4ae3919f74896a6b8565" IssueInstant="2022-10-14T14:11:49.590Z" Version="2.0">
    <saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">https://accounts.google.com/o/saml2?idpid=</saml2:Issuer>
    <saml2p:Status>
        <saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"></saml2p:StatusCode>
    </saml2p:Status>
    <saml2:Assertion xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" ID="_346001c5708ffd118c40edbc0c72fc60" IssueInstant="2022-10-14T14:11:49.590Z" Version="2.0">
        <saml2:Issuer>https://accounts.google.com/o/saml2?idpid=</saml2:Issuer>
        <saml2:Subject>
            <saml2:NameID Format="urn:oasis:names:tc:SAML:2.0:nameid-format:persistent">jens@goauthentik.io</saml2:NameID>
            <saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
                <saml2:SubjectConfirmationData InResponseTo="_157fb504b59f4ae3919f74896a6b8565" NotOnOrAfter="2022-10-14T14:16:49.590Z" Recipient="https://127.0.0.1:9443/source/saml/google/acs/"></saml2:SubjectConfirmationData>
            </saml2:SubjectConfirmation>
        </saml2:Subject>
        <saml2:Conditions NotBefore="2022-10-14T14:06:49.590Z" NotOnOrAfter="2022-10-14T14:16:49.590Z">
            <saml2:AudienceRestriction>
                <saml2:Audience>https://accounts.google.com/o/saml2?idpid=</saml2:Audience>
            </saml2:AudienceRestriction>
        </saml2:Conditions>
        <saml2:AttributeStatement>
            <saml2:Attribute Name="name">
                <saml2:AttributeValue xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:anyType">foo</saml2:AttributeValue>
            </saml2:Attribute>
            <saml2:Attribute Name="sn">
                <saml2:AttributeValue xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:anyType">bar</saml2:AttributeValue>
            </saml2:Attribute>
            <saml2:Attribute Name="email">
                <saml2:AttributeValue xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:anyType">foo@bar.baz</saml2:AttributeValue>
            </saml2:Attribute>
        </saml2:AttributeStatement>
        <saml2:AuthnStatement AuthnInstant="2022-10-14T12:16:21.000Z" SessionIndex="_346001c5708ffd118c40edbc0c72fc60">
            <saml2:AuthnContext>
                <saml2:AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:unspecified</saml2:AuthnContextClassRef>
            </saml2:AuthnContext>
        </saml2:AuthnStatement>
    </saml2:Assertion>
</saml2p:Response>
"""


class TestResponseProcessor(TestCase):
    """Test ResponseProcessor"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            slug=generate_id(),
            issuer="authentik",
            allow_idp_initiated=True,
            pre_authentication_flow=create_test_flow(),
        )

    def test_status_error(self):
        """Test error status"""
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(RESPONSE_ERROR.encode()).decode()}
        )

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        with self.assertRaisesMessage(
            ValueError,
            (
                "Invalid request, ACS Url in request http://localhost:9000/source/saml/google/acs/ "
                "doesn't match configured ACS Url https://127.0.0.1:9443/source/saml/google/acs/."
            ),
        ):
            ResponseProcessor(self.source, request).parse()

    def test_success(self):
        """Test success"""
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(RESPONSE_SUCCESS.encode()).decode()}
        )

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(
            sfm.enroll_info,
            {"email": "foo@bar.baz", "name": "foo", "sn": "bar", "username": "jens@goauthentik.io"},
        )
