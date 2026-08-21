from plistlib import PlistFormat, loads

from defusedxml.lxml import fromstring
from django.test import RequestFactory
from rest_framework.test import APITestCase

from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    ApplePSSOAuthenticationMethod,
    ApplePSSOAuthenticationPolicy,
    ApplePSSOBiometricRequirement,
    EnrollmentToken,
)
from authentik.endpoints.facts import OSFamily
from authentik.lib.generators import generate_id


def _platform_sso(config: str) -> dict:
    """Return the PlatformSSO dict from a generated macOS profile."""
    data = loads(config, fmt=PlistFormat.FMT_XML)
    return next(
        payload["PlatformSSO"]
        for payload in data["PayloadContent"]
        if payload.get("PayloadType") == "com.apple.extensiblesso"
    )


class TestAgentConnector(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
        )
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.factory = RequestFactory()

    def test_generate_mdm_macos(self):
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        self.assertIsNotNone(res.validated_data)
        data = loads(res.validated_data["config"], fmt=PlistFormat.FMT_XML)
        self.assertEqual(data["PayloadContent"][0]["RegistrationToken"], self.token.key)
        self.assertEqual(data["PayloadContent"][0]["URL"], "http://testserver/")
        # With the default configuration Platform SSO stays passive: no enforcement
        # policies are emitted, only the always-present login frequency.
        psso = _platform_sso(res.validated_data["config"])
        self.assertNotIn("LoginPolicy", psso)
        self.assertNotIn("UnlockPolicy", psso)
        self.assertNotIn("FileVaultPolicy", psso)
        self.assertEqual(psso["LoginFrequency"], 64800)

    def test_biometric_policies_default_off(self):
        """No requirement means no policy at all. The modifiers are deliberately ignored:
        PasswordFallback on its own would demand nothing while looking like it demands
        something, so the agent must be told to leave the OptionSet untouched."""
        self.assertEqual(self.connector.apple_psso_biometric_policies, [])
        self.connector.apple_psso_biometric_reuse_during_unlock = True
        self.assertEqual(self.connector.apple_psso_biometric_policies, [])

    def test_biometric_policies_password_fallback_is_default(self):
        """Selecting a requirement must carry the password fallback with it. Without it a
        user whose Touch ID is cancelled, failing, or never enrolled — every Mac with no
        Touch ID hardware — cannot use the key at all."""
        self.connector.apple_psso_biometric_requirement = ApplePSSOBiometricRequirement.CURRENT_SET
        self.assertEqual(
            self.connector.apple_psso_biometric_policies,
            ["touch_id_or_watch_current_set", "password_fallback"],
        )

    def test_biometric_policies_all_options(self):
        self.connector.apple_psso_biometric_requirement = ApplePSSOBiometricRequirement.ANY
        self.connector.apple_psso_biometric_reuse_during_unlock = True
        self.assertEqual(
            self.connector.apple_psso_biometric_policies,
            ["touch_id_or_watch_any", "password_fallback", "reuse_during_unlock"],
        )

    def test_biometric_policies_fallback_can_be_disabled(self):
        self.connector.apple_psso_biometric_requirement = ApplePSSOBiometricRequirement.ANY
        self.connector.apple_psso_biometric_password_fallback = False
        self.assertEqual(self.connector.apple_psso_biometric_policies, ["touch_id_or_watch_any"])

    def test_generate_mdm_macos_psso_policies(self):
        """Configured Apple Platform SSO policies must appear in the generated profile as
        arrays of policy strings (matching ee/psso/example.mobileconfig); policies left at
        their default must be omitted so Platform SSO keeps its passive behaviour."""
        self.connector.apple_psso_authentication_method = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso_login_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso_unlock_policy = ApplePSSOAuthenticationPolicy.ATTEMPT
        self.connector.apple_psso_login_frequency = 7200
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["LoginPolicy"], ["RequireAuthentication"])
        self.assertEqual(psso["UnlockPolicy"], ["AttemptAuthentication"])
        self.assertEqual(psso["LoginFrequency"], 7200)
        # filevault left at the default "none" -> key omitted entirely
        self.assertNotIn("FileVaultPolicy", psso)

    def test_generate_mdm_macos_deterministic(self):
        """Two downloads of an unchanged configuration must be byte-identical. Random
        PayloadUUIDs would make every download read as a changed profile to the MDM,
        and redelivering the extensiblesso payload with a new UUID deregisters
        Platform SSO on every enrolled Mac."""
        request = self.factory.get("/")
        first = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        second = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        self.assertEqual(first.validated_data["config"], second.validated_data["config"])

    def test_generate_mdm_macos_authentication_method_default(self):
        """The Secure Enclave key mode stays the default, so existing enrollments keep the
        behaviour they had before the method was configurable."""
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["AuthenticationMethod"], "UserSecureEnclaveKey")

    def test_generate_mdm_macos_authentication_method_password(self):
        self.connector.apple_psso_authentication_method = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["AuthenticationMethod"], "Password")

    def test_generate_mdm_macos_policies_omitted_in_secure_enclave_mode(self):
        """Apple documents the login/unlock/FileVault policies as applying only to the
        password method, so configuring them in Secure Enclave key mode must not write keys
        macOS will ignore."""
        self.connector.apple_psso_login_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso_unlock_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso_filevault_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertNotIn("LoginPolicy", psso)
        self.assertNotIn("UnlockPolicy", psso)
        self.assertNotIn("FileVaultPolicy", psso)

    def test_biometric_policies_omitted_in_password_mode(self):
        """There is no user Secure Enclave key in password mode, so a biometric policy
        guarding it would be meaningless."""
        self.connector.apple_psso_authentication_method = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso_biometric_requirement = ApplePSSOBiometricRequirement.ANY
        self.assertEqual(self.connector.apple_psso_biometric_policies, [])

    def test_generate_mdm_macos_grace_periods(self):
        """The grace periods are modifiers inside each policy array, not standalone keys, so
        the flag has to travel with every policy being enforced alongside the duration."""
        self.connector.apple_psso_authentication_method = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso_login_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso_unlock_policy = ApplePSSOAuthenticationPolicy.ATTEMPT
        self.connector.apple_psso_authentication_grace_period = 3600
        self.connector.apple_psso_offline_grace_period = 7200
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(
            psso["LoginPolicy"],
            ["RequireAuthentication", "AllowAuthenticationGracePeriod", "AllowOfflineGracePeriod"],
        )
        self.assertEqual(
            psso["UnlockPolicy"],
            ["AttemptAuthentication", "AllowAuthenticationGracePeriod", "AllowOfflineGracePeriod"],
        )
        self.assertEqual(psso["AuthenticationGracePeriod"], 3600)
        self.assertEqual(psso["OfflineGracePeriod"], 7200)
        # filevault left at "none" -> no policy to modify, so the key stays absent
        self.assertNotIn("FileVaultPolicy", psso)

    def test_generate_mdm_macos_touch_id_unlock_modifier(self):
        """AllowTouchIDOrWatchForUnlock only means something on an UnlockPolicy of
        RequireAuthentication, so it lands there and nowhere else — and disabling the
        connector option keeps it out even then."""
        self.connector.apple_psso_authentication_method = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso_login_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso_unlock_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(
            psso["UnlockPolicy"], ["RequireAuthentication", "AllowTouchIDOrWatchForUnlock"]
        )
        self.assertEqual(psso["LoginPolicy"], ["RequireAuthentication"])

        self.connector.apple_psso_unlock_allow_touch_id_or_watch = False
        self.connector.save()
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["UnlockPolicy"], ["RequireAuthentication"])

        self.connector.apple_psso_unlock_allow_touch_id_or_watch = True
        self.connector.apple_psso_unlock_policy = ApplePSSOAuthenticationPolicy.ATTEMPT
        self.connector.save()
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["UnlockPolicy"], ["AttemptAuthentication"])

    def test_generate_mdm_macos_grace_period_without_policy(self):
        """A duration with no policy to attach to would be inert, so neither the flag nor
        the duration is written."""
        self.connector.apple_psso_authentication_method = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso_authentication_grace_period = 3600
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertNotIn("AuthenticationGracePeriod", psso)

    def test_generate_mdm_macos_exempt_accounts_and_user_creation(self):
        self.connector.apple_psso_authentication_method = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso_non_platform_sso_accounts = ["breakglass", "localadmin"]
        self.connector.apple_psso_enable_create_user_at_login = True
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["NonPlatformSSOAccounts"], ["breakglass", "localadmin"])
        self.assertTrue(psso["EnableCreateUserAtLogin"])

    def test_generate_mdm_macos_password_only_keys_omitted_in_secure_enclave_mode(self):
        """Every one of these is documented as password-method behaviour, so none of them
        may leak into a Secure Enclave key profile."""
        self.connector.apple_psso_non_platform_sso_accounts = ["breakglass"]
        self.connector.apple_psso_enable_create_user_at_login = True
        self.connector.apple_psso_authentication_grace_period = 3600
        self.connector.apple_psso_offline_grace_period = 7200
        self.connector.apple_psso_login_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        for key in (
            "NonPlatformSSOAccounts",
            "EnableCreateUserAtLogin",
            "AuthenticationGracePeriod",
            "OfflineGracePeriod",
            "LoginPolicy",
        ):
            self.assertNotIn(key, psso)

    def test_generate_mdm_windows(self):
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.windows, request, self.token
        )
        self.assertIsNotNone(res.validated_data)
        config = res.validated_data["config"]
        fromstring(f"<root>{config}</root>")
        self.assertIn(self.token.key, config)
        self.assertIn("http://testserver/", config)
