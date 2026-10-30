"""Test WebAuthn RP configs"""

from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.brands.models import Brand
from authentik.brands.utils import DEFAULT_BRAND
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice, WebAuthnRPConfig
from authentik.stages.authenticator_webauthn.utils import get_origin, get_rp_id


class TestWebAuthnRPConfigAPI(APITestCase):
    """Test WebAuthnRPConfig API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)

    def test_create(self):
        """Test valid config creation"""
        response = self.client.post(
            reverse("authentik_api:webauthnrpconfig-list"),
            data={
                "name": generate_id(),
                "rp_id": "sso.example.com",
                "origins": [
                    "https://sso.example.com",
                    "https://accounts.example.net:8443",
                    "android:apk-key-hash:bE5w-Nl3cCq9XU10dBl2z7MAOTgvEnUKvyKqtISycdk",
                ],
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_create_invalid_origins(self):
        """Test origin format validation"""
        for origin in [
            "http://sso.example.com",
            "https://sso.example.com/",
            "https://sso.example.com/path",
            "https://sso.example.com?query=1",
            "https://*.example.com",
            "https://SSO.example.com",
            "sso.example.com",
            "android:apk-key-hash:",
            "android:apk-key-hash:not/base64url+",
            "https://user@sso.example.com",
            "https://sso.example.com:443",
            "https://192.0.2.10",
            "https://[2001:db8::1]",
            "https://sso.example.com:70000",
            "https://sso.example.com:ab",
            "https://:8443",
        ]:
            with self.subTest(origin=origin):
                response = self.client.post(
                    reverse("authentik_api:webauthnrpconfig-list"),
                    data={
                        "name": generate_id(),
                        "rp_id": "sso.example.com",
                        "origins": [origin],
                    },
                )
                self.assertEqual(response.status_code, 400)

    def test_create_empty_origins(self):
        """Test at least one origin is required"""
        response = self.client.post(
            reverse("authentik_api:webauthnrpconfig-list"),
            data={
                "name": generate_id(),
                "rp_id": "sso.example.com",
                "origins": [],
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_create_invalid_rp_id(self):
        """Test RP ID must be a domain name"""
        for rp_id in [
            "https://sso.example.com",
            "sso.example.com:9443",
            "*.example.com",
            "sso.example.com.",
            "ss\u00f6.example.com",
        ]:
            with self.subTest(rp_id=rp_id):
                response = self.client.post(
                    reverse("authentik_api:webauthnrpconfig-list"),
                    data={
                        "name": generate_id(),
                        "rp_id": rp_id,
                        "origins": ["https://sso.example.com"],
                    },
                )
                self.assertEqual(response.status_code, 400)

    def test_rp_id_normalized(self):
        """Test RP ID is lowercased on save"""
        response = self.client.post(
            reverse("authentik_api:webauthnrpconfig-list"),
            data={
                "name": generate_id(),
                "rp_id": "SSO.Example.com",
                "origins": ["https://sso.example.com"],
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["rp_id"], "sso.example.com")

    def test_rp_id_immutable(self):
        """Test RP ID cannot be changed after creation"""
        config = WebAuthnRPConfig.objects.create(
            name=generate_id(),
            rp_id="sso.example.com",
            origins=["https://sso.example.com"],
        )
        response = self.client.patch(
            reverse("authentik_api:webauthnrpconfig-detail", kwargs={"pk": config.pk}),
            data={"rp_id": "other.example.com"},
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(
            reverse("authentik_api:webauthnrpconfig-detail", kwargs={"pk": config.pk}),
            data={"rp_id": "sso.example.com", "origins": ["https://sso.example.com"]},
        )
        self.assertEqual(response.status_code, 200)


class TestWebAuthnRPConfigUtils(APITestCase):
    """Test RP ID/origin resolution"""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.config = WebAuthnRPConfig.objects.create(
            name=generate_id(),
            rp_id="sso.example.com",
            origins=["https://sso.example.com", "https://accounts.example.net"],
        )

    def test_without_brand(self):
        """Test fallback to request host without a brand"""
        request = self.factory.get("/")
        self.assertEqual(get_rp_id(request), "testserver")
        self.assertEqual(get_origin(request), "http://testserver")

    def test_brand_without_config(self):
        """Test fallback to request host with a brand without RP config"""
        request = self.factory.get("/")
        request.brand = Brand.objects.create(domain=generate_id())
        self.assertEqual(get_rp_id(request), "testserver")
        self.assertEqual(get_origin(request), "http://testserver")

    def test_default_unsaved_brand(self):
        """Test fallback with the unsaved fallback brand"""
        request = self.factory.get("/")
        request.brand = DEFAULT_BRAND
        self.assertEqual(get_rp_id(request), "testserver")
        self.assertEqual(get_origin(request), "http://testserver")

    def test_brand_with_config(self):
        """Test RP ID and origins from the brand's RP config"""
        request = self.factory.get("/")
        request.brand = Brand.objects.create(domain=generate_id(), webauthn_rp_config=self.config)
        self.assertEqual(get_rp_id(request), "sso.example.com")
        self.assertEqual(
            get_origin(request), ["https://sso.example.com", "https://accounts.example.net"]
        )

    def test_brand_with_config_empty_origins(self):
        """Test a config without origins does not fall back to the request origin"""
        config = WebAuthnRPConfig.objects.create(
            name=generate_id(), rp_id="empty.example.com", origins=[]
        )
        request = self.factory.get("/")
        request.brand = Brand.objects.create(domain=generate_id(), webauthn_rp_config=config)
        self.assertEqual(get_rp_id(request), "empty.example.com")
        self.assertEqual(get_origin(request), [])

    def test_host_with_port(self):
        """Test port is stripped from the request host"""
        request = self.factory.get("/", SERVER_PORT="9000")
        self.assertEqual(get_rp_id(request), "testserver")
        self.assertEqual(get_origin(request), "http://testserver:9000")


class TestWebAuthnRelatedOrigins(APITestCase):
    """Test /.well-known/webauthn"""

    def test_no_config(self):
        """Test 404 when no config matches the request host"""
        response = self.client.get("/.well-known/webauthn")
        self.assertEqual(response.status_code, 404)

    def test_config_other_host(self):
        """Test 404 when a config exists for a different RP ID"""
        WebAuthnRPConfig.objects.create(
            name=generate_id(),
            rp_id="sso.example.com",
            origins=["https://sso.example.com"],
        )
        response = self.client.get("/.well-known/webauthn")
        self.assertEqual(response.status_code, 404)

    def test_config_matching_host(self):
        """Test document with https origins only for the matching RP ID"""
        WebAuthnRPConfig.objects.create(
            name=generate_id(),
            rp_id="testserver",
            origins=[
                "https://testserver",
                "https://accounts.example.net",
                "android:apk-key-hash:bE5w-Nl3cCq9XU10dBl2z7MAOTgvEnUKvyKqtISycdk",
            ],
        )
        response = self.client.get("/.well-known/webauthn")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response["Cache-Control"], "max-age=300")
        self.assertIn("Host", response["Vary"])
        self.assertJSONEqual(
            response.content.decode(),
            {"origins": ["https://testserver", "https://accounts.example.net"]},
        )


class TestBrandRPConfigPreFlight(APITestCase):
    """Test the lockout pre-flight when assigning an RP config to a brand"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)
        self.brand = Brand.objects.create(domain="brand.example.org")
        self.config = WebAuthnRPConfig.objects.create(
            name=generate_id(),
            rp_id="sso.example.com",
            origins=["https://sso.example.com"],
        )

    def attach(self):
        return self.client.patch(
            reverse("authentik_api:brand-detail", kwargs={"pk": self.brand.pk}),
            data={"webauthn_rp_config": str(self.config.pk)},
        )

    def test_attach_no_devices(self):
        """Test attaching with no existing devices"""
        self.assertEqual(self.attach().status_code, 200)

    def test_attach_blocked(self):
        """Test attaching is blocked while a user's only authenticator would break"""
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="auth.brand.example.org")
        response = self.attach()
        self.assertEqual(response.status_code, 400)
        self.assertIn("webauthn_rp_config", response.json())

    def test_attach_with_fallback_factor(self):
        """Test attaching passes when affected users have another authenticator"""
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="auth.brand.example.org")
        TOTPDevice.objects.create(user=user, name=generate_id(), confirmed=True)
        self.assertEqual(self.attach().status_code, 200)

    def test_attach_unrelated_devices(self):
        """Test devices under other brands' hosts don't block"""
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="other.example.net")
        self.assertEqual(self.attach().status_code, 200)

    def test_attach_matching_devices(self):
        """Test devices already bound to the config's RP ID don't block"""
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="sso.example.com")
        self.assertEqual(self.attach().status_code, 200)

    def test_attach_default_brand_blocked(self):
        """Test the default brand considers devices under any host"""
        self.brand.default = True
        self.brand.save()
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="other.example.net")
        response = self.attach()
        self.assertEqual(response.status_code, 400)

    def test_switch_config_blocked(self):
        """Test switching configs is blocked for devices under the old config's RP ID"""
        old_config = WebAuthnRPConfig.objects.create(
            name=generate_id(),
            rp_id="old.example.net",
            origins=["https://old.example.net"],
        )
        self.brand.webauthn_rp_config = old_config
        self.brand.save()
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="old.example.net")
        response = self.attach()
        self.assertEqual(response.status_code, 400)
        self.assertIn("webauthn_rp_config", response.json())

    def test_default_flip_blocked(self):
        """Test making a config-bearing brand the default re-runs the pre-flight"""
        Brand.objects.filter(default=True).update(default=False)
        self.brand.webauthn_rp_config = self.config
        self.brand.save()
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="other.example.net")
        response = self.client.patch(
            reverse("authentik_api:brand-detail", kwargs={"pk": self.brand.pk}),
            data={"default": True},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("webauthn_rp_config", response.json())

    def test_unrelated_edit_not_blocked(self):
        """Test edits that change neither config nor scope skip the pre-flight"""
        self.brand.webauthn_rp_config = self.config
        self.brand.save()
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="auth.brand.example.org")
        response = self.client.patch(
            reverse("authentik_api:brand-detail", kwargs={"pk": self.brand.pk}),
            data={
                "branding_title": generate_id(),
                "domain": self.brand.domain,
                "default": self.brand.default,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_detach(self):
        """Test detaching a config is not blocked"""
        self.brand.webauthn_rp_config = self.config
        self.brand.save()
        user = create_test_user()
        WebAuthnDevice.objects.create(user=user, name=generate_id(), rp_id="sso.example.com")
        response = self.client.patch(
            reverse("authentik_api:brand-detail", kwargs={"pk": self.brand.pk}),
            data={"webauthn_rp_config": None},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_protected(self):
        """Test a config referenced by a brand cannot be deleted"""
        self.brand.webauthn_rp_config = self.config
        self.brand.save()
        response = self.client.delete(
            reverse("authentik_api:webauthnrpconfig-detail", kwargs={"pk": self.config.pk})
        )
        self.assertEqual(response.status_code, 400)
