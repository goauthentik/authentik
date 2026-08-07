"""bsky DPoP HTTP client tests"""

import jwt
from django.core.cache import cache
from django.test import TestCase
from requests.exceptions import HTTPError
from requests_mock import Mocker

from authentik.sources.bsky.client import dpop_request
from authentik.sources.bsky.models import BskySource
from authentik.sources.bsky.resolver import ResolutionError


class TestDpopRequest(TestCase):
    """Test dpop_request"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")
        cache.clear()

    def test_happy_path_no_nonce(self):
        """Test a request that succeeds on the first attempt, no nonce required"""
        with Mocker() as mocker:
            mocker.post("https://authserver.example.com/oauth/par", json={"request_uri": "abc"})
            result = dpop_request(
                self.source, "POST", "https://authserver.example.com/oauth/par", data={}
            )
            self.assertEqual(result, {"request_uri": "abc"})

    def test_nonce_retry_succeeds(self):
        """Test a 400/401 use_dpop_nonce response triggers one retry with a nonce, then succeeds"""
        with Mocker() as mocker:
            mocker.post(
                "https://authserver.example.com/oauth/par",
                [
                    {
                        "status_code": 400,
                        "json": {"error": "use_dpop_nonce"},
                        "headers": {"DPoP-Nonce": "server-nonce"},
                    },
                    {"status_code": 200, "json": {"request_uri": "abc"}},
                ],
            )
            result = dpop_request(
                self.source, "POST", "https://authserver.example.com/oauth/par", data={}
            )
            self.assertEqual(result, {"request_uri": "abc"})

    def test_nonce_retry_exhausted_raises(self):
        """Test ResolutionError raised when both attempts come back use_dpop_nonce"""
        with Mocker() as mocker:
            mocker.post(
                "https://authserver.example.com/oauth/par",
                status_code=400,
                json={"error": "use_dpop_nonce"},
                headers={"DPoP-Nonce": "server-nonce"},
            )
            with self.assertRaises(ResolutionError):
                dpop_request(
                    self.source, "POST", "https://authserver.example.com/oauth/par", data={}
                )

    def test_nonce_cache_is_scoped_per_host(self):
        """Test a cached nonce from one host isn't sent to a different host (the bsky/PDS bug)"""
        with Mocker() as mocker:
            mocker.post(
                "https://authserver.example.com/oauth/par",
                [
                    {
                        "status_code": 400,
                        "json": {"error": "use_dpop_nonce"},
                        "headers": {"DPoP-Nonce": "authserver-nonce"},
                    },
                    {"status_code": 200, "json": {"request_uri": "abc"}},
                ],
            )
            dpop_request(self.source, "POST", "https://authserver.example.com/oauth/par", data={})

            # A different host has never returned a nonce yet, so the first proof sent to
            # it must not carry the authserver's nonce (or any nonce at all).
            mocker.get("https://pds.example.com/xrpc/some.method", json={"ok": True})
            dpop_request(self.source, "GET", "https://pds.example.com/xrpc/some.method")

            pds_request = next(r for r in mocker.request_history if "pds.example.com" in r.url)
            proof = pds_request.headers["DPoP"]
            payload = jwt.decode(proof, options={"verify_signature": False})
            self.assertNotIn("nonce", payload)

    def test_other_error_status_raises_immediately(self):
        """Test a non-use_dpop_nonce error response raises via raise_for_status without retrying"""
        with Mocker() as mocker:
            mocker.post(
                "https://authserver.example.com/oauth/par",
                status_code=400,
                json={"error": "invalid_request"},
            )
            with self.assertRaises(HTTPError):
                dpop_request(
                    self.source, "POST", "https://authserver.example.com/oauth/par", data={}
                )
            self.assertEqual(len(mocker.request_history), 1)
