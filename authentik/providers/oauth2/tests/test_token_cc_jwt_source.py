"""Test token view"""

from datetime import datetime, timedelta
from json import loads

from django.test import RequestFactory
from django.urls import reverse
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_CLIENT_CREDENTIALS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
    TOKEN_TYPE,
)
from authentik.core.models import USERNAME_MAX_LENGTH, Application, Group, User
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import (
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.sources.oauth.models import OAuthSource, OAuthSourcePropertyMapping


class TestTokenClientCredentialsJWTSource(OAuthTestCase):
    """Test token (client_credentials, with JWT) view"""

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
        self.cert = create_test_cert()

        jwk = JWKSView().get_jwk_for_key(self.other_cert, "sig")
        self.source: OAuthSource = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url="http://foo",
            access_token_url=f"http://{generate_id()}",
            profile_url="http://foo",
            oidc_well_known_url="",
            oidc_jwks_url="",
            oidc_jwks={
                "keys": [jwk],
            },
        )

        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=self.cert,
            grant_types=[GrantType.CLIENT_CREDENTIALS],
        )
        self.provider.jwt_federation_sources.add(self.source)
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)

    def test_invalid_type(self):
        """test invalid type"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "foo",
                "client_assertion": "foo.bar",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_jwt(self):
        """test invalid JWT"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": "foo.bar",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_signature(self):
        """test invalid JWT"""
        token = self.helper_provider.encode(
            {
                "sub": "foo",
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
                "client_assertion": token + "foo",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_expired(self):
        """test invalid JWT"""
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() - timedelta(hours=2),
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
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_no_app(self):
        """test invalid JWT"""
        self.app.provider = None
        self.app.save()
        token = self.helper_provider.encode(
            {
                "sub": "foo",
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
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_access_denied(self):
        """test invalid JWT"""
        group = Group.objects.create(name="foo")
        PolicyBinding.objects.create(
            group=group,
            target=self.app,
            order=0,
        )
        token = self.helper_provider.encode(
            {
                "sub": "foo",
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
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_successful(self):
        """test successful"""
        token = self.helper_provider.encode(
            {
                "sub": "foo",
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

        user = User.objects.filter(username=f"{self.provider.name}-foo").first()
        self.assertIsNotNone(user)

        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        _, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        self.assertEqual(
            jwt["given_name"], "Autogenerated user from application test (client credentials JWT)"
        )
        self.assertEqual(jwt["preferred_username"], "test-foo")

    def test_successful_mapping(self):
        """test successful"""
        test_username = ("mapped-foo" + ("a" * 150))[:USERNAME_MAX_LENGTH]
        mapping = OAuthSourcePropertyMapping.objects.create(
            name="test-mapping",
            expression="""return {
                "email": oauth_userinfo.get("email"),
                "name": oauth_userinfo.get("name"),
                "username": oauth_userinfo.get("username"),
            }""",
        )
        self.source.user_property_mappings.add(mapping)

        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "email": "test-user@example.com",
                "name": "Mapped Test User",
                "username": "mapped-foo" + ("a" * 150),
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

        user = User.objects.filter(username=test_username).first()
        self.assertIsNotNone(user)

        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        key_obj, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=key_obj.public_key(),
            algorithms=[alg],
            audience=self.provider.client_id,
        )

        self.assertEqual(jwt["email"], "test-user@example.com")
        self.assertEqual(jwt["given_name"], "Mapped Test User")
        self.assertEqual(jwt["preferred_username"], test_username)

    def test_successful_group_mapping(self):
        """Test that groups returned by property mappings are applied to the auto-generated user.

        Regression test: previously, the 'groups' key returned by user property mapping
        expressions was silently ignored when exchanging a federated JWT (e.g. a SPIRE SVID)
        for an Authentik access token via the client_credentials grant. Only scalar fields
        such as username/name/email/attributes were propagated; group membership was not.
        """
        from authentik.core.models import SourceGroupMatchingModes

        # Use name_link mode so the pre-existing "MyApp Users" group is found by name,
        # matching the typical real-world configuration (see authentik.yaml in ai-lab).
        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_LINK
        self.source.save()
        target_group = Group.objects.create(name="MyApp Users")
        mapping = OAuthSourcePropertyMapping.objects.create(
            name="spire-group-mapping",
            expression="""return {
                "username": info.get("sub"),
                "name": info.get("sub"),
                "groups": ["MyApp Users"],
            }""",
        )
        self.source.user_property_mappings.add(mapping)

        token = self.helper_provider.encode(
            {
                "sub": "spire-workload//cluster.local/ns/default/sa/myapp",
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

        user = User.objects.filter(
            username="spire-workload//cluster.local/ns/default/sa/myapp"
        ).first()
        self.assertIsNotNone(user)
        self.assertIn(target_group, user.groups.all(), "User should be in mapped group")

    def test_group_mapping_name_link_existing_group(self):
        """Test that name_link mode correctly links to an existing group without duplicating it."""
        from authentik.core.models import SourceGroupMatchingModes

        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_LINK
        self.source.save()
        existing_group = Group.objects.create(name="Existing Group")
        mapping = OAuthSourcePropertyMapping.objects.create(
            name="group-link-mapping",
            expression="""return {"username": info.get("sub"), "groups": ["Existing Group"]}""",
        )
        self.source.user_property_mappings.add(mapping)

        token = self.helper_provider.encode(
            {"sub": "link-test-user", "exp": datetime.now() + timedelta(hours=2)}
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
        user = User.objects.filter(username="link-test-user").first()
        self.assertIsNotNone(user)
        # Must be the same group object — name_link must not create a duplicate
        self.assertIn(existing_group, user.groups.all())
        self.assertEqual(Group.objects.filter(name="Existing Group").count(), 1)

    def test_group_mapping_reruns_update_membership(self):
        """Test that group membership is updated on subsequent token requests."""
        from authentik.core.models import SourceGroupMatchingModes

        # Use name_link so that pre-created groups are found by name
        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_LINK
        self.source.save()

        group_a = Group.objects.create(name="Group A")
        group_b = Group.objects.create(name="Group B")
        mapping = OAuthSourcePropertyMapping.objects.create(
            name="dynamic-group-mapping",
            expression="""
groups = info.get("groups", [])
return {"username": info.get("sub"), "groups": groups}
""",
        )
        self.source.user_property_mappings.add(mapping)

        def _exchange(groups: list[str]):
            token = self.helper_provider.encode(
                {
                    "sub": "update-test-user",
                    "groups": groups,
                    "exp": datetime.now() + timedelta(hours=2),
                }
            )
            return self.client.post(
                reverse("authentik_providers_oauth2:token"),
                {
                    "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                    "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                    "client_id": self.provider.client_id,
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": token,
                },
            )

        # First request: user should be in Group A only
        self.assertEqual(_exchange(["Group A"]).status_code, 200)
        user = User.objects.get(username="update-test-user")
        self.assertIn(group_a, user.groups.all())
        self.assertNotIn(group_b, user.groups.all())

        # Second request: user should be in Group B only (Group A removed)
        self.assertEqual(_exchange(["Group B"]).status_code, 200)
        user.refresh_from_db()
        self.assertNotIn(group_a, user.groups.all())
        self.assertIn(group_b, user.groups.all())
