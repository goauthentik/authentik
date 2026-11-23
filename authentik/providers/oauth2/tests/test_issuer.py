"""Test the canonical issuer used by issuer-sensitive checks"""

from django.test import RequestFactory, TestCase

from authentik.brands.models import Brand
from authentik.brands.utils import get_brand_for_request
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_flow
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.issuer import (
    CONFIG_TRUSTED_ISSUER_ORIGINS,
    UntrustedIssuer,
    check_issuer_host,
    normalize_origin,
    trusted_issuer_origins,
)
from authentik.providers.oauth2.models import IssuerMode, OAuth2Provider


class TestCanonicalIssuer(TestCase):
    """OAuth2Provider.get_canonical_issuer"""

    def setUp(self):
        Brand.objects.all().delete()
        # The fallback for hosts no other brand matches
        Brand.objects.create(domain="authentik-default", default=True)
        Brand.objects.create(domain="authentik.company")
        self.factory = RequestFactory()
        self.app = Application.objects.create(name=generate_id(), slug="x")
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        self.app.provider = self.provider
        self.app.save()

    def request(self, host: str, secure: bool = True):
        return self.factory.post("/application/o/token/", HTTP_HOST=host, secure=secure)

    def assert_refused(self, host: str, reason: str, secure: bool = True):
        with self.assertRaises(UntrustedIssuer) as ctx:
            self.provider.get_canonical_issuer(self.request(host, secure))
        self.assertEqual(ctx.exception.reason, reason)

    def test_brand_domain(self):
        """A host matching a brand's domain is trusted, and the issuer is the usual one"""
        request = self.request("authentik.company")
        self.assertEqual(
            self.provider.get_canonical_issuer(request),
            "https://authentik.company/application/o/x/",
        )
        self.assertEqual(
            self.provider.get_canonical_issuer(request), self.provider.get_issuer(request)
        )

    def test_brand_subdomain(self):
        """Brands match subdomains, and so does the trust"""
        self.assertEqual(
            self.provider.get_canonical_issuer(self.request("sso.authentik.company")),
            "https://sso.authentik.company/application/o/x/",
        )

    def test_brand_domain_case(self):
        """Hosts are trusted case-insensitively, like brands match them"""
        check_issuer_host(self.request("Authentik.Company"))

    def test_global_issuer_mode(self):
        """Global issuer mode is checked the same way"""
        self.provider.issuer_mode = IssuerMode.GLOBAL
        self.provider.save()
        self.assertEqual(
            self.provider.get_canonical_issuer(self.request("authentik.company")),
            "https://authentik.company/",
        )
        self.assert_refused("evil.example", "host_not_trusted")

    def test_spoofed_host(self):
        """A host that only reaches the default brand as the fallback is refused, although
        `get_issuer` happily builds an issuer from it"""
        request = self.request("evil.example")
        self.assertEqual(self.provider.get_issuer(request), "https://evil.example/application/o/x/")
        self.assert_refused("evil.example", "host_not_trusted")

    def test_suffix_not_subdomain(self):
        """A host that merely ends with a brand's domain isn't a subdomain of it"""
        self.assert_refused("evilauthentik.company", "host_not_trusted")

    def test_default_brand_domain(self):
        """The default brand is trusted when the host matches its domain"""
        Brand.objects.filter(default=True).update(domain="idp.example")
        get_brand_for_request.cache_clear()
        self.assertEqual(
            self.provider.get_canonical_issuer(self.request("idp.example")),
            "https://idp.example/application/o/x/",
        )

    def test_no_brands(self):
        """Without any brand, nothing is trusted (the in-memory fallback brand doesn't count)"""
        Brand.objects.all().delete()
        self.assert_refused("fallback", "host_not_trusted")
        self.assert_refused("authentik.company", "host_not_trusted")

    def test_provider_without_application(self):
        """A provider without an application has no issuer"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        with self.assertRaises(UntrustedIssuer) as ctx:
            provider.get_canonical_issuer(self.request("authentik.company"))
        self.assertEqual(ctx.exception.reason, "no_issuer")

    def test_configured_origins(self):
        """Configured origins are the only trusted ones: brands no longer count, and the
        scheme and port must match"""
        with CONFIG.patch(CONFIG_TRUSTED_ISSUER_ORIGINS, ["https://idp.example/"]):
            self.assertEqual(
                self.provider.get_canonical_issuer(self.request("idp.example")),
                "https://idp.example/application/o/x/",
            )
            self.assertEqual(
                self.provider.get_canonical_issuer(self.request("idp.example:443")),
                "https://idp.example:443/application/o/x/",
            )
            self.assert_refused("authentik.company", "origin_not_trusted")
            self.assert_refused("evil.example", "origin_not_trusted")
            self.assert_refused("idp.example:8443", "origin_not_trusted")
            self.assert_refused("idp.example", "origin_not_trusted", secure=False)

    def test_configured_origins_env_string(self):
        """A comma-separated string, as set from the environment, works too"""
        with CONFIG.patch(
            CONFIG_TRUSTED_ISSUER_ORIGINS, "https://idp.example, http://localhost:9000"
        ):
            self.assertEqual(
                trusted_issuer_origins(),
                frozenset({"https://idp.example", "http://localhost:9000"}),
            )
            check_issuer_host(self.request("localhost:9000", secure=False))
            self.assert_refused("localhost:9000", "origin_not_trusted")

    def test_configured_origins_invalid_entries(self):
        """Entries that aren't origins are ignored; if none is left, brands decide"""
        with CONFIG.patch(
            CONFIG_TRUSTED_ISSUER_ORIGINS,
            ["https://idp.example/path", "ftp://idp.example", "idp.example", ""],
        ):
            self.assertEqual(trusted_issuer_origins(), frozenset())
            check_issuer_host(self.request("authentik.company"))
            self.assert_refused("idp.example", "host_not_trusted")

    def test_normalize_origin(self):
        """Origins are normalized, and anything else is rejected"""
        for value, expected in [
            ("https://IdP.Example", "https://idp.example"),
            ("HTTPS://idp.example:443/", "https://idp.example"),
            ("http://idp.example:80", "http://idp.example"),
            ("https://idp.example:8443", "https://idp.example:8443"),
            ("https://[::1]:9443", "https://[::1]:9443"),
            ("https://idp.example/path", None),
            ("https://idp.example?q", None),
            ("https://idp.example#f", None),
            ("https://user@idp.example", None),
            ("https://idp.example:99999", None),
            ("https://", None),
            ("idp.example", None),
            ("ftp://idp.example", None),
        ]:
            with self.subTest(value=value):
                self.assertEqual(normalize_origin(value), expected)
