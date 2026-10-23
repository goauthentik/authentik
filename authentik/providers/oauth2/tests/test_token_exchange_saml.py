"""Test token exchange for SAML Responses"""

from base64 import b64decode
from datetime import datetime, timedelta
from json import loads

from django.http import HttpResponse
from django.urls import reverse
from django.utils.timezone import now
from lxml import etree  # nosec

from authentik.common.oauth.constants import (
    GRANT_TYPE_TOKEN_EXCHANGE,
    TOKEN_TYPE_URI_ACCESS_TOKEN,
    TOKEN_TYPE_URI_SAML2,
)
from authentik.common.saml.constants import NS_MAP
from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import AccessToken, GrantType, OAuth2Provider
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.saml.models import SAMLProvider


class TestTokenExchangeSAML(OAuthTestCase):
    """Test exchanging a JWT for a SAML Response (RFC 8693)"""

    def setUp(self) -> None:
        super().setUp()
        # The provider that issued the subject token
        self.other_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=create_test_cert(),
            grant_types=[],
        )

        # The provider performing the exchange
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=create_test_cert(),
            grant_types=[GrantType.TOKEN_EXCHANGE],
        )
        self.provider.jwt_federation_providers.add(self.other_provider)
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=self.provider)

        # The SAML provider a Response is requested for via `audience`
        self.saml_provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            acs_url="https://signin.aws.amazon.com/saml",
            audience="urn:amazon:webservices",
            signing_kp=create_test_cert(),
        )
        self.saml_provider.jwt_federation_providers.add(self.provider)
        self.saml_app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.saml_provider
        )

        self.user = create_test_user()
        self.subject_token = self.other_provider.encode(
            {"sub": "foo", "exp": datetime.now() + timedelta(hours=2)}
        )
        AccessToken.objects.create(
            provider=self.other_provider,
            token=self.subject_token,
            user=self.user,
            auth_time=now(),
        )

    def _exchange(self, **extra) -> HttpResponse:
        """Run an otherwise-valid SAML exchange, with `extra` merged into the request"""
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "requested_token_type": TOKEN_TYPE_URI_SAML2,
                "audience": str(self.saml_app.pbm_uuid),
                **extra,
            },
        )

    def assert_error(self, response: HttpResponse, error: str):
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], error)

    def test_successful(self):
        """test exchanging a JWT for a signed SAML Response"""
        response = self._exchange()
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())
        self.assertEqual(body["issued_token_type"], TOKEN_TYPE_URI_SAML2)
        self.assertEqual(body["token_type"], "N_A")
        root = etree.fromstring(b64decode(body["access_token"]))  # nosec
        self.assertEqual(root.attrib["Destination"], "https://signin.aws.amazon.com/saml")
        self.assertEqual(
            root.xpath("//saml:Audience", namespaces=NS_MAP)[0].text, "urn:amazon:webservices"
        )
        self.assertTrue(root.xpath("//ds:Signature", namespaces=NS_MAP))
        self.assertFalse(AccessToken.objects.filter(provider=self.provider).exists())

    def test_missing_audience(self):
        """test that a SAML Response requires an audience"""
        self.assert_error(self._exchange(audience=[]), "invalid_target")

    def test_not_federated(self):
        """test a SAML provider that does not federate with the requesting provider"""
        self.saml_provider.jwt_federation_providers.clear()
        self.assert_error(self._exchange(), "invalid_target")

    def test_policy_denied(self):
        """test that the SAML application's policies gate the exchange"""
        PolicyBinding.objects.create(
            group=Group.objects.create(name=generate_id()), target=self.saml_app, order=0
        )
        self.assert_error(self._exchange(), "invalid_grant")
