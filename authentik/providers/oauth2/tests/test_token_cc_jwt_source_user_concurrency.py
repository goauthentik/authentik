"""Test which user a client_credentials JWT from a federation source is issued for while other
writes run"""

from datetime import datetime, timedelta
from threading import Event, Thread, current_thread
from unittest.mock import patch

from django.db import connection
from django.db.models import QuerySet
from django.test import Client, RequestFactory, TransactionTestCase
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_CLIENT_CREDENTIALS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.core.models import (
    USER_ATTRIBUTE_GENERATED,
    Application,
    User,
    UserQuerySet,
    UserTypes,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.providers.oauth2.views.token import TokenParams
from authentik.sources.oauth.models import OAuthSource


class TestTokenClientCredentialsJWTSourceUserConcurrency(TransactionTestCase):
    """Test which user a client_credentials JWT from a federation source is issued for while
    other writes run"""

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

    def test_username_taken_during_request(self):
        """A JWT is refused when its username is taken while the request runs, and that user is
        left unchanged"""

        def take_username():
            create_test_admin_user("alice")
            connection.close()

        def take_username_before_write(queryset, *args, **kwargs):
            # On another connection, as a concurrent request would
            thread = Thread(target=take_username)
            thread.start()
            thread.join()
            return QuerySet.update_or_create(queryset, *args, **kwargs)

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
        with patch.object(UserQuerySet, "update_or_create", take_username_before_write):
            with self.assertRaises(TokenError) as cm:
                TokenParams.parse(request, self.provider, self.provider.client_id, "")
        self.assertEqual(cm.exception.error, "invalid_grant")
        self.assertEqual(cm.exception.cause, "conflicting_user_exists")
        user = User.objects.get(username="alice")
        self.assertEqual(user.type, UserTypes.INTERNAL)
        self.assertEqual(user.path, "users")
        self.assertEqual(user.attributes, {})

    def test_new_subject(self):
        """A second request for a new subject gets a token while the first one is still
        running"""
        written = Event()
        resume = Event()

        def pause_first_after_write(queryset, *args, **kwargs):
            result = QuerySet.update_or_create(queryset, *args, **kwargs)
            if current_thread().name == "first":
                written.set()
                resume.wait(10)
            return result

        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "preferred_username": "build",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        data = {
            "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
            "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
            "client_id": self.provider.client_id,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": token,
        }
        responses = {}

        def request_first():
            responses["first"] = Client().post(reverse("authentik_providers_oauth2:token"), data)
            connection.close()

        with patch.object(UserQuerySet, "update_or_create", pause_first_after_write):
            first = Thread(target=request_first, name="first")
            first.start()
            self.assertTrue(written.wait(10))
            second = self.client.post(reverse("authentik_providers_oauth2:token"), data)
            resume.set()
            first.join()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(responses["first"].status_code, 200)

    def test_generated_user(self):
        """A second request for an existing generated service account gets a token while the
        first one is still running"""
        User.objects.create(
            username="build",
            type=UserTypes.SERVICE_ACCOUNT,
            path="goauthentik.io/sources/idp",
            attributes={USER_ATTRIBUTE_GENERATED: True},
        )
        written = Event()
        resume = Event()

        def pause_first_after_write(queryset, *args, **kwargs):
            result = QuerySet.update_or_create(queryset, *args, **kwargs)
            if current_thread().name == "first":
                written.set()
                resume.wait(10)
            return result

        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "preferred_username": "build",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        data = {
            "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
            "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
            "client_id": self.provider.client_id,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": token,
        }
        responses = {}

        def request_first():
            responses["first"] = Client().post(reverse("authentik_providers_oauth2:token"), data)
            connection.close()

        with patch.object(UserQuerySet, "update_or_create", pause_first_after_write):
            first = Thread(target=request_first, name="first")
            first.start()
            self.assertTrue(written.wait(10))
            second = self.client.post(reverse("authentik_providers_oauth2:token"), data)
            resume.set()
            first.join()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(responses["first"].status_code, 200)
