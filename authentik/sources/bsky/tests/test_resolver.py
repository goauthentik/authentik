"""bsky identity resolver tests"""

from unittest.mock import patch

from django.test import TestCase
from dns.exception import DNSException
from requests_mock import Mocker

from authentik.sources.bsky.resolver import (
    ResolutionError,
    get_authserver_metadata,
    get_authserver_url,
    get_pds_endpoint,
    resolve_did,
    resolve_handle,
    resolve_identity,
)

DID_DOC = {
    "id": "did:plc:test",
    "alsoKnownAs": ["at://user.bsky.social"],
    "service": [
        {
            "id": "#atproto_pds",
            "type": "AtprotoPersonalDataServer",
            "serviceEndpoint": "https://pds.example.com",
        }
    ],
}

PROTECTED_RESOURCE = {
    "resource": "https://pds.example.com",
    "authorization_servers": ["https://authserver.example.com"],
}

AUTHSERVER_METADATA = {
    "issuer": "https://authserver.example.com",
    "authorization_endpoint": "https://authserver.example.com/oauth/authorize",
    "token_endpoint": "https://authserver.example.com/oauth/token",
    "pushed_authorization_request_endpoint": "https://authserver.example.com/oauth/par",
    "require_pushed_authorization_requests": True,
    "token_endpoint_auth_methods_supported": ["private_key_jwt"],
}


class FakeTXTRecord:
    """Minimal stand-in for a dnspython TXT rdata object"""

    def __init__(self, *strings: bytes):
        self.strings = list(strings)


class TestResolveHandle(TestCase):
    """Test resolve_handle"""

    def test_resolve_handle_dns(self):
        """Test handle resolves via DNS TXT record"""
        with patch(
            "dns.resolver.resolve",
            return_value=[FakeTXTRecord(b"did=did:plc:test")],
        ) as mock_resolve:
            self.assertEqual(resolve_handle("user.bsky.social"), "did:plc:test")
            mock_resolve.assert_called_once_with("_atproto.user.bsky.social", "TXT")

    def test_resolve_handle_dns_wrong_record(self):
        """Test DNS TXT records present but none matching did= fall through to HTTP"""
        with patch(
            "dns.resolver.resolve",
            return_value=[FakeTXTRecord(b"v=something-unrelated")],
        ):
            with Mocker() as mocker:
                mocker.get(
                    "https://user.bsky.social/.well-known/atproto-did",
                    text="did:plc:test",
                )
                self.assertEqual(resolve_handle("user.bsky.social"), "did:plc:test")

    def test_resolve_handle_http_fallback(self):
        """Test handle resolves via .well-known/atproto-did when DNS fails"""
        with patch("dns.resolver.resolve", side_effect=DNSException()):
            with Mocker() as mocker:
                mocker.get(
                    "https://user.bsky.social/.well-known/atproto-did",
                    text="did:plc:test",
                )
                self.assertEqual(resolve_handle("user.bsky.social"), "did:plc:test")

    def test_resolve_handle_http_wrong_body(self):
        """Test a 200 response whose body isn't did:-prefixed is treated as not found"""
        with patch("dns.resolver.resolve", side_effect=DNSException()):
            with Mocker() as mocker:
                mocker.get(
                    "https://user.bsky.social/.well-known/atproto-did",
                    text="not-a-did",
                )
                with self.assertRaises(ResolutionError):
                    resolve_handle("user.bsky.social")

    def test_resolve_handle_not_found(self):
        """Test ResolutionError raised when both DNS and HTTP fail"""
        with patch("dns.resolver.resolve", side_effect=DNSException()):
            with Mocker() as mocker:
                mocker.get(
                    "https://user.bsky.social/.well-known/atproto-did",
                    status_code=404,
                )
                with self.assertRaises(ResolutionError):
                    resolve_handle("user.bsky.social")


class TestResolveDid(TestCase):
    """Test resolve_did"""

    def test_resolve_did_plc(self):
        """Test did:plc:* resolves via plc.directory"""
        with Mocker() as mocker:
            mocker.get("https://plc.directory/did:plc:test", json=DID_DOC)
            self.assertEqual(resolve_did("did:plc:test"), DID_DOC)

    def test_resolve_did_web_simple_domain(self):
        """Test did:web:<domain> resolves via https://<domain>/.well-known/did.json"""
        with Mocker() as mocker:
            mocker.get("https://example.com/.well-known/did.json", json=DID_DOC)
            self.assertEqual(resolve_did("did:web:example.com"), DID_DOC)

    def test_resolve_did_web_with_path_segments(self):
        """Test did:web:<domain>:<path>:<segments> decodes colons as path separators"""
        with Mocker() as mocker:
            mocker.get(
                "https://example.com/user/alice/.well-known/did.json",
                json=DID_DOC,
            )
            self.assertEqual(resolve_did("did:web:example.com:user:alice"), DID_DOC)

    def test_resolve_did_web_with_encoded_port(self):
        """Test did:web:<domain>%3A<port> decodes to a port, not a path segment"""
        with Mocker() as mocker:
            mocker.get("https://example.com:8443/.well-known/did.json", json=DID_DOC)
            self.assertEqual(resolve_did("did:web:example.com%3A8443"), DID_DOC)

    def test_resolve_did_unsupported_method(self):
        """Test ResolutionError raised for an unsupported DID method"""
        with self.assertRaises(ResolutionError):
            resolve_did("did:example:test")


class TestGetPdsEndpoint(TestCase):
    """Test get_pds_endpoint"""

    def test_get_pds_endpoint_found(self):
        """Test PDS service endpoint extracted from DID document"""
        self.assertEqual(get_pds_endpoint(DID_DOC), "https://pds.example.com")

    def test_get_pds_endpoint_missing(self):
        """Test ResolutionError raised when no #atproto_pds service is present"""
        with self.assertRaises(ResolutionError):
            get_pds_endpoint({"service": []})


class TestGetAuthserverUrl(TestCase):
    """Test get_authserver_url"""

    def test_get_authserver_url(self):
        """Test authorization server URL extracted from protected-resource metadata"""
        with Mocker() as mocker:
            mocker.get(
                "https://pds.example.com/.well-known/oauth-protected-resource",
                json=PROTECTED_RESOURCE,
            )
            self.assertEqual(
                get_authserver_url("https://pds.example.com"),
                "https://authserver.example.com",
            )


class TestGetAuthserverMetadata(TestCase):
    """Test get_authserver_metadata"""

    def test_get_authserver_metadata_supported(self):
        """Test metadata returned as-is when PAR + private_key_jwt are supported"""
        with Mocker() as mocker:
            mocker.get(
                "https://authserver.example.com/.well-known/oauth-authorization-server",
                json=AUTHSERVER_METADATA,
            )
            self.assertEqual(
                get_authserver_metadata("https://authserver.example.com"),
                AUTHSERVER_METADATA,
            )

    def test_get_authserver_metadata_no_par(self):
        """Test ResolutionError raised when require_pushed_authorization_requests is False"""
        metadata = {**AUTHSERVER_METADATA, "require_pushed_authorization_requests": False}
        with Mocker() as mocker:
            mocker.get(
                "https://authserver.example.com/.well-known/oauth-authorization-server",
                json=metadata,
            )
            with self.assertRaises(ResolutionError):
                get_authserver_metadata("https://authserver.example.com")

    def test_get_authserver_metadata_no_private_key_jwt(self):
        """Test ResolutionError raised when private_key_jwt isn't in the supported auth methods"""
        metadata = {**AUTHSERVER_METADATA, "token_endpoint_auth_methods_supported": ["none"]}
        with Mocker() as mocker:
            mocker.get(
                "https://authserver.example.com/.well-known/oauth-authorization-server",
                json=metadata,
            )
            with self.assertRaises(ResolutionError):
                get_authserver_metadata("https://authserver.example.com")


class TestResolveIdentity(TestCase):
    """Test resolve_identity"""

    def _mock_chain(self, mocker: Mocker):
        """Stub the DID doc -> protected-resource -> authserver metadata chain,
        shared by every test below (handle resolution is stubbed separately)"""
        mocker.get("https://plc.directory/did:plc:test", json=DID_DOC)
        mocker.get(
            "https://pds.example.com/.well-known/oauth-protected-resource",
            json=PROTECTED_RESOURCE,
        )
        mocker.get(
            "https://authserver.example.com/.well-known/oauth-authorization-server",
            json=AUTHSERVER_METADATA,
        )

    def test_resolve_identity_from_handle(self):
        """Test full resolution chain starting from a handle"""
        with patch(
            "dns.resolver.resolve",
            return_value=[FakeTXTRecord(b"did=did:plc:test")],
        ):
            with Mocker() as mocker:
                self._mock_chain(mocker)
                identity = resolve_identity("user.bsky.social")

        self.assertEqual(identity.did, "did:plc:test")
        self.assertEqual(identity.handle, "user.bsky.social")
        self.assertEqual(identity.pds_url, "https://pds.example.com")
        self.assertEqual(identity.authserver_url, "https://authserver.example.com")
        self.assertEqual(identity.authserver_metadata, AUTHSERVER_METADATA)

    def test_resolve_identity_from_did(self):
        """Test full resolution chain starting from a did: identifier"""
        with Mocker() as mocker:
            self._mock_chain(mocker)
            identity = resolve_identity("did:plc:test")

        self.assertEqual(identity.did, "did:plc:test")
        self.assertEqual(identity.handle, "user.bsky.social")
        self.assertEqual(identity.pds_url, "https://pds.example.com")
        self.assertEqual(identity.authserver_url, "https://authserver.example.com")

    def test_resolve_identity_handle_spoofing_rejected(self):
        """Test ResolutionError raised when the DID doc's alsoKnownAs doesn't claim the handle"""
        with patch(
            "dns.resolver.resolve",
            return_value=[FakeTXTRecord(b"did=did:plc:test")],
        ):
            with Mocker() as mocker:
                # DID_DOC's alsoKnownAs claims "user.bsky.social", not this handle
                mocker.get("https://plc.directory/did:plc:test", json=DID_DOC)
                with self.assertRaises(ResolutionError):
                    resolve_identity("attacker.bsky.social")
