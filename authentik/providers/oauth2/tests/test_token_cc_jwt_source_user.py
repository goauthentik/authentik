"""Test which user a client_credentials JWT from a federation source is issued for"""

from datetime import datetime, timedelta

from django.test import RequestFactory
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_CLIENT_CREDENTIALS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.core.models import USER_ATTRIBUTE_GENERATED, Application, User, UserTypes
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    AccessToken,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.providers.oauth2.views.token import TokenParams
from authentik.sources.oauth.models import OAuthSource


class TestTokenClientCredentialsJWTSourceUser(OAuthTestCase):
    """Test which user a client_credentials JWT from a federation source is issued for"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.other_cert = create_test_cert()
        # Provider used as a helper to sign JWTs with the same key as the OAuth source has
        self.helper_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=self.other_cert,
        )
        self.source = OAuthSource.objects.create(
            name="idp",
            slug="idp",
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url="http://foo",
            access_token_url=f"http://{generate_id()}",
            profile_url="http://foo",
            oidc_well_known_url="",
            oidc_jwks_url="",
            oidc_jwks={"keys": [JWKSView().get_jwk_for_key(self.other_cert, "sig")]},
        )
        self.provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=create_test_cert(),
            grant_types=[GrantType.CLIENT_CREDENTIALS],
        )
        self.provider.jwt_federation_sources.add(self.source)
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)

    def test_new_subject(self):
        """A JWT from a new subject is issued for a generated service account"""
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "preferred_username": "build",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="build")
        self.assertEqual(user.type, UserTypes.SERVICE_ACCOUNT)
        self.assertTrue(user.attributes[USER_ATTRIBUTE_GENERATED])
        self.assertEqual(AccessToken.objects.filter(user=user).count(), 1)

    def test_generated_user(self):
        """A JWT is issued for the generated service account with its username"""
        user = User.objects.create(
            username="build",
            type=UserTypes.SERVICE_ACCOUNT,
            path="goauthentik.io/sources/idp",
            attributes={USER_ATTRIBUTE_GENERATED: True},
        )
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "preferred_username": "build",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AccessToken.objects.filter(user=user).count(), 1)

    def test_username_in_use(self):
        """A JWT whose username belongs to another user is refused, and that user is left
        unchanged"""
        user = create_test_admin_user("alice")
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "preferred_username": "alice",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        with self.assertRaises(TokenError) as cm:
            TokenParams.parse(request, self.provider, self.provider.client_id, "")
        self.assertEqual(cm.exception.error, "invalid_grant")
        self.assertEqual(cm.exception.cause, "conflicting_user_exists")
        user.refresh_from_db()
        self.assertEqual(user.type, UserTypes.INTERNAL)
        self.assertEqual(user.path, "users")
        self.assertEqual(user.name, "alice")
        self.assertEqual(user.email, "alice@goauthentik.io")
        self.assertEqual(user.attributes, {})

    def test_default_username_in_use(self):
        """A JWT without a username is refused when the username derived from its subject
        belongs to another user"""
        user = create_test_user("test-foo")
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        with self.assertRaises(TokenError) as cm:
            TokenParams.parse(request, self.provider, self.provider.client_id, "")
        self.assertEqual(cm.exception.error, "invalid_grant")
        self.assertEqual(cm.exception.cause, "conflicting_user_exists")
        user.refresh_from_db()
        self.assertEqual(user.type, UserTypes.INTERNAL)
        self.assertEqual(user.path, "users")

    def test_username_in_use_by_service_account(self):
        """A JWT whose username belongs to a service account that wasn't generated is refused"""
        user = User.objects.create(username="ci-bot", type=UserTypes.SERVICE_ACCOUNT)
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "preferred_username": "ci-bot",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        with self.assertRaises(TokenError) as cm:
            TokenParams.parse(request, self.provider, self.provider.client_id, "")
        self.assertEqual(cm.exception.error, "invalid_grant")
        self.assertEqual(cm.exception.cause, "conflicting_user_exists")
        user.refresh_from_db()
        self.assertEqual(user.path, "users")
        self.assertEqual(user.attributes, {})

    def test_username_in_use_by_generated_user(self):
        """A JWT whose username belongs to a generated user that isn't a service account is
        refused"""
        user = User.objects.create(
            username="ak-bar-transient",
            attributes={USER_ATTRIBUTE_GENERATED: True},
        )
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "preferred_username": "ak-bar-transient",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        with self.assertRaises(TokenError) as cm:
            TokenParams.parse(request, self.provider, self.provider.client_id, "")
        self.assertEqual(cm.exception.error, "invalid_grant")
        self.assertEqual(cm.exception.cause, "conflicting_user_exists")
        user.refresh_from_db()
        self.assertEqual(user.type, UserTypes.INTERNAL)
        self.assertEqual(user.path, "users")
