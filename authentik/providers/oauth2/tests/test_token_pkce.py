"""Test token view"""

from base64 import b64encode, urlsafe_b64encode
from hashlib import sha256

from django.test import RequestFactory
from django.urls import reverse

from authentik.common.oauth.constants import GRANT_TYPE_AUTHORIZATION_CODE
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.crypto.generators import generate_id
from authentik.providers.oauth2.models import (
    AuthorizationCode,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestTokenPKCE(OAuthTestCase):
    """Test token view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.app = Application.objects.create(name=generate_id(), slug="test")

    def test_pkce_missing_in_authorize(self):
        """Test PKCE with code_challenge in authorize request
        and missing verifier in token request"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        challenge = generate_id()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        # Step 1, initiate params and get redirect to flow
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertEqual(
            response.url,
            f"foo://localhost?code={code.code}&state={state}",
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                # Missing the code_verifier here
                "redirect_uri": "foo://localhost",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertJSONEqual(
            response.content,
            {
                "error": "invalid_grant",
                "error_description": (
                    "The provided authorization grant or refresh token is invalid, expired, "
                    "revoked, does not match the redirection URI used in the authorization "
                    "request, or was issued to another client"
                ),
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_pkce_missing_in_token(self):
        """Test PKCE with missing code_challenge in authorization request but verifier
        set in token request"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        # Step 1, initiate params and get redirect to flow
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
                # "code_challenge": challenge,
                # "code_challenge_method": "S256",
            },
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertEqual(
            response.url,
            f"foo://localhost?code={code.code}&state={state}",
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "code_verifier": generate_id(),
                "redirect_uri": "foo://localhost",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertJSONEqual(
            response.content,
            {
                "error": "invalid_grant",
                "error_description": (
                    "The provided authorization grant or refresh token is invalid, expired, "
                    "revoked, does not match the redirection URI used in the authorization "
                    "request, or was issued to another client"
                ),
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_pkce_correct_s256(self):
        """Test full with pkce"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        verifier = generate_id()
        challenge = (
            urlsafe_b64encode(sha256(verifier.encode("ascii")).digest())
            .decode("utf-8")
            .replace("=", "")
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        # Step 1, initiate params and get redirect to flow
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertEqual(
            response.url,
            f"foo://localhost?code={code.code}&state={state}",
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "code_verifier": verifier,
                "redirect_uri": "foo://localhost",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200)

    def test_pkce_correct_plain(self):
        """Test full with pkce"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        verifier = generate_id()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        # Step 1, initiate params and get redirect to flow
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
                "code_challenge": verifier,
            },
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertEqual(
            response.url,
            f"foo://localhost?code={code.code}&state={state}",
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "code_verifier": verifier,
                "redirect_uri": "foo://localhost",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200)
