"""google Type tests"""

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory

from authentik.common.tests import dummy_get_response
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.google import (
    GoogleOAuthRedirect,
    GoogleType,
)

# https://developers.google.com/identity/protocols/oauth2/openid-connect?hl=en
GOOGLE_USER = {
    "id": "1324813249123401234",
    "email": "foo@bar.baz",
    "verified_email": True,
    "name": "foo bar",
    "given_name": "foo",
    "family_name": "bar",
    "picture": "",
    "locale": "en",
}


class TestTypeGoogle(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source: OAuthSource = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="google",
            authorization_url="",
            profile_url="",
            consumer_key="foo",
        )
        self.request_factory = RequestFactory()

    def test_enroll_context(self):
        """Test Google Enrollment context"""
        ak_context = GoogleType().get_base_user_properties(source=self.source, info=GOOGLE_USER)
        self.assertEqual(ak_context["email"], GOOGLE_USER["email"])
        self.assertEqual(ak_context["name"], GOOGLE_USER["name"])

    def test_authorize_url(self):
        """Test authorize URL"""
        request = self.request_factory.get("/")
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        redirect = GoogleOAuthRedirect(request=request).get_redirect_url(
            source_slug=self.source.slug
        )
        self.assertEqual(
            redirect,
            (
                f"https://accounts.google.com/o/oauth2/auth?client_id={self.source.consumer_key}&re"
                "direct_uri=http%3A%2F%2Ftestserver%2Fsource%2Foauth%2Fcallback%2Ftest%2F&response_"
                f"type=code&state={request.session['oauth-client-test-request-state']}&scope="
                "email%20profile"
            ),
        )

    def test_authorize_url_additional(self):
        """Test authorize URL"""
        request = self.request_factory.get("/")
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        self.source.additional_scopes = "foo"
        self.source.save()
        redirect = GoogleOAuthRedirect(request=request).get_redirect_url(
            source_slug=self.source.slug
        )
        self.assertEqual(
            redirect,
            (
                f"https://accounts.google.com/o/oauth2/auth?client_id={self.source.consumer_key}&re"
                "direct_uri=http%3A%2F%2Ftestserver%2Fsource%2Foauth%2Fcallback%2Ftest%2F&response_"
                f"type=code&state={request.session['oauth-client-test-request-state']}&scope="
                "email%20foo%20profile"
            ),
        )

    def test_authorize_url_additional_replace(self):
        """Test authorize URL"""
        request = self.request_factory.get("/")
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        self.source.additional_scopes = "*foo"
        self.source.save()
        redirect = GoogleOAuthRedirect(request=request).get_redirect_url(
            source_slug=self.source.slug
        )
        self.assertEqual(
            redirect,
            (
                f"https://accounts.google.com/o/oauth2/auth?client_id={self.source.consumer_key}&re"
                "direct_uri=http%3A%2F%2Ftestserver%2Fsource%2Foauth%2Fcallback%2Ftest%2F&response_"
                f"type=code&state={request.session['oauth-client-test-request-state']}&scope="
                "foo"
            ),
        )
