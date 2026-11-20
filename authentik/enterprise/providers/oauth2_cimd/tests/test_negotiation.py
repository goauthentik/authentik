"""Effective-capability negotiation"""

from django.test import SimpleTestCase

from authentik.enterprise.providers.oauth2_cimd.errors import UnsupportedClient
from authentik.enterprise.providers.oauth2_cimd.jwks import validate_jwks
from authentik.enterprise.providers.oauth2_cimd.metadata import validate_metadata
from authentik.enterprise.providers.oauth2_cimd.negotiation import (
    MANAGED_PROFILE,
    PUBLIC_PROFILE,
    ProfileName,
    negotiate,
)
from authentik.enterprise.providers.oauth2_cimd.tests.utils import (
    CLIENT_ID,
    JWKS_URI,
    managed_document,
    public_document,
    public_jwk,
)

KEYS = validate_jwks({"keys": [public_jwk("EC", kid="k1")]})


def metadata(**overrides):
    return validate_metadata(public_document(**overrides), CLIENT_ID)


class TestPublicProfile(SimpleTestCase):
    """Public profile"""

    def assertUnsupported(self, md, code, profile=PUBLIC_PROFILE, keys=None):
        with self.assertRaises(UnsupportedClient) as ctx:
            negotiate(md, profile, keys)
        self.assertEqual(ctx.exception.code, code)

    def test_none_without_keys(self):
        caps = negotiate(metadata(), PUBLIC_PROFILE)
        self.assertEqual(caps.profile, ProfileName.PUBLIC)
        self.assertEqual(caps.token_endpoint_auth_method, "none")
        self.assertFalse(caps.confidential)
        self.assertTrue(caps.pkce_required)
        self.assertEqual(caps.pkce_methods, frozenset(("S256",)))
        self.assertEqual(caps.grant_types, frozenset(("authorization_code", "refresh_token")))
        self.assertEqual(caps.response_types, frozenset(("code",)))

    def test_default_method(self):
        """No method declared means `none`"""
        caps = negotiate(metadata(token_endpoint_auth_method=None), PUBLIC_PROFILE)
        self.assertEqual(caps.token_endpoint_auth_method, "none")

    def test_plural_prefers_supported(self):
        md = metadata(
            token_endpoint_auth_method=None,
            token_endpoint_auth_methods_supported=["private_key_jwt", "none"],
            jwks_uri=JWKS_URI,
        )
        caps = negotiate(md, PUBLIC_PROFILE)
        self.assertEqual(caps.token_endpoint_auth_method, "none")
        self.assertFalse(caps.confidential)

    def test_keys_do_not_make_confidential(self):
        md = metadata(jwks={"keys": [public_jwk("EC")]})
        caps = negotiate(md, PUBLIC_PROFILE, md.jwks)
        self.assertFalse(caps.confidential)

    def test_only_private_key_jwt(self):
        md = metadata(token_endpoint_auth_method="private_key_jwt", jwks_uri=JWKS_URI)
        self.assertUnsupported(md, "auth_method_unsupported", keys=KEYS)

    def test_unknown_method_only(self):
        self.assertUnsupported(
            metadata(token_endpoint_auth_method="tls_client_auth"), "auth_method_unsupported"
        )

    def test_unsupported_grants_dropped(self):
        caps = negotiate(
            metadata(
                grant_types=["authorization_code", "implicit", "client_credentials", "password"],
                response_types=["code", "token", "id_token"],
            ),
            PUBLIC_PROFILE,
        )
        self.assertEqual(caps.grant_types, frozenset(("authorization_code",)))
        self.assertEqual(caps.response_types, frozenset(("code",)))

    def test_refresh_requires_declaration(self):
        caps = negotiate(metadata(grant_types=None), PUBLIC_PROFILE)
        self.assertEqual(caps.grant_types, frozenset(("authorization_code",)))

    def test_no_common_grant(self):
        self.assertUnsupported(metadata(grant_types=["implicit"]), "no_common_grant")
        self.assertUnsupported(metadata(grant_types=[]), "no_common_grant")
        self.assertUnsupported(metadata(response_types=["token"]), "no_common_grant")

    def test_requires_authorization_code(self):
        self.assertUnsupported(metadata(grant_types=["refresh_token"]), "required_grant_missing")

    def test_requires_redirect_uris(self):
        self.assertUnsupported(metadata(redirect_uris=None), "redirect_uris_required")

    def test_restrict(self):
        profile = PUBLIC_PROFILE.restrict(
            grant_types=frozenset(("authorization_code", "client_credentials"))
        )
        self.assertEqual(profile.grant_types, frozenset(("authorization_code",)))
        caps = negotiate(metadata(), profile)
        self.assertEqual(caps.grant_types, frozenset(("authorization_code",)))
        with self.assertRaises(UnsupportedClient):
            negotiate(metadata(), PUBLIC_PROFILE.restrict(grant_types=frozenset()))


class TestManagedProfile(SimpleTestCase):
    """Managed profile"""

    def assertUnsupported(self, md, code, keys=None):
        with self.assertRaises(UnsupportedClient) as ctx:
            negotiate(md, MANAGED_PROFILE, keys)
        self.assertEqual(ctx.exception.code, code)

    def test_private_key_jwt(self):
        md = validate_metadata(managed_document(), CLIENT_ID)
        caps = negotiate(md, MANAGED_PROFILE, KEYS)
        self.assertEqual(caps.profile, ProfileName.MANAGED)
        self.assertEqual(caps.token_endpoint_auth_method, "private_key_jwt")
        self.assertTrue(caps.confidential)
        self.assertEqual(
            caps.grant_types,
            frozenset(("authorization_code", "refresh_token")),
        )
        self.assertTrue(caps.pkce_required)

    def test_client_credentials_only(self):
        md = validate_metadata(
            managed_document(grant_types=["client_credentials"], redirect_uris=None), CLIENT_ID
        )
        self.assertUnsupported(md, "no_common_grant", KEYS)

    def test_declares_none(self):
        """Declaring `none` can't bypass the required method"""
        md = metadata(token_endpoint_auth_method="none", jwks_uri=JWKS_URI)
        self.assertUnsupported(md, "auth_method_unsupported", KEYS)
        self.assertUnsupported(metadata(), "auth_method_unsupported")

    def test_declares_none_and_private_key_jwt_without_keys(self):
        md = metadata(
            token_endpoint_auth_method=None,
            token_endpoint_auth_methods_supported=["none", "private_key_jwt"],
        )
        self.assertUnsupported(md, "signing_keys_required")

    def test_no_key_metadata(self):
        md = validate_metadata(managed_document(jwks_uri=None), CLIENT_ID)
        self.assertUnsupported(md, "signing_keys_required", KEYS)

    def test_no_usable_keys(self):
        md = validate_metadata(managed_document(), CLIENT_ID)
        self.assertUnsupported(md, "signing_keys_required", None)
        empty = validate_jwks({"keys": [public_jwk("RSA", use="enc")]})
        self.assertUnsupported(md, "signing_keys_required", empty)

    def test_inline_keys(self):
        md = validate_metadata(
            managed_document(jwks_uri=None, jwks={"keys": [public_jwk("RSA", kid="a")]}),
            CLIENT_ID,
        )
        caps = negotiate(md, MANAGED_PROFILE, md.jwks)
        self.assertEqual(caps.token_endpoint_auth_method, "private_key_jwt")
