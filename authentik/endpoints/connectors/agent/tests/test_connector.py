from plistlib import PlistFormat, loads

from defusedxml.lxml import fromstring
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
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
        # No policies by default, only the login frequency
        psso = _platform_sso(res.validated_data["config"])
        self.assertNotIn("LoginPolicy", psso)
        self.assertNotIn("UnlockPolicy", psso)
        self.assertNotIn("FileVaultPolicy", psso)
        self.assertEqual(psso["LoginFrequency"], 64800)

    def test_biometric_policies_default_off(self):
        """No requirement means no policies, even with modifiers set"""
        self.assertEqual(self.connector.apple_psso_biometric_policies, [])
        self.connector.apple_psso["biometric_reuse_during_unlock"] = True
        self.assertEqual(self.connector.apple_psso_biometric_policies, [])

    def test_biometric_policies_password_fallback_is_default(self):
        """Password fallback is on by default"""
        self.connector.apple_psso["biometric_requirement"] = (
            ApplePSSOBiometricRequirement.CURRENT_SET
        )
        self.assertEqual(
            self.connector.apple_psso_biometric_policies,
            ["touch_id_or_watch_current_set", "password_fallback"],
        )

    def test_biometric_policies_all_options(self):
        self.connector.apple_psso["biometric_requirement"] = ApplePSSOBiometricRequirement.ANY
        self.connector.apple_psso["biometric_reuse_during_unlock"] = True
        self.assertEqual(
            self.connector.apple_psso_biometric_policies,
            ["touch_id_or_watch_any", "password_fallback", "reuse_during_unlock"],
        )

    def test_biometric_policies_fallback_can_be_disabled(self):
        self.connector.apple_psso["biometric_requirement"] = ApplePSSOBiometricRequirement.ANY
        self.connector.apple_psso["biometric_password_fallback"] = False
        self.assertEqual(self.connector.apple_psso_biometric_policies, ["touch_id_or_watch_any"])

    def test_generate_mdm_macos_psso_policies(self):
        """Configured policies are written as arrays, default ones are omitted"""
        self.connector.apple_psso["authentication_method"] = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso["login_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso["unlock_policy"] = ApplePSSOAuthenticationPolicy.ATTEMPT
        self.connector.apple_psso["login_frequency"] = 7200
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
        """Generating the same configuration twice gives identical output"""
        request = self.factory.get("/")
        first = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        second = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        self.assertEqual(first.validated_data["config"], second.validated_data["config"])

    def test_generate_mdm_macos_authentication_method_default(self):
        """Secure Enclave key is the default method"""
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["AuthenticationMethod"], "UserSecureEnclaveKey")

    def test_generate_mdm_macos_authentication_method_password(self):
        self.connector.apple_psso["authentication_method"] = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["AuthenticationMethod"], "Password")

    def test_generate_mdm_macos_policies_omitted_in_secure_enclave_mode(self):
        """Policies are only written for the password method"""
        self.connector.apple_psso["login_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso["unlock_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso["filevault_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
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
        """No biometric policies for the password method"""
        self.connector.apple_psso["authentication_method"] = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso["biometric_requirement"] = ApplePSSOBiometricRequirement.ANY
        self.assertEqual(self.connector.apple_psso_biometric_policies, [])

    def test_generate_mdm_macos_grace_periods(self):
        """Grace periods are added to each enforced policy"""
        self.connector.apple_psso["authentication_method"] = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso["login_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso["unlock_policy"] = ApplePSSOAuthenticationPolicy.ATTEMPT
        self.connector.apple_psso["authentication_grace_period"] = 3600
        self.connector.apple_psso["offline_grace_period"] = 7200
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
        """The Touch ID modifier is only added to an unlock policy of require"""
        self.connector.apple_psso["authentication_method"] = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso["login_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso["unlock_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
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

        self.connector.apple_psso["unlock_allow_touch_id_or_watch"] = False
        self.connector.save()
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["UnlockPolicy"], ["RequireAuthentication"])

        self.connector.apple_psso["unlock_allow_touch_id_or_watch"] = True
        self.connector.apple_psso["unlock_policy"] = ApplePSSOAuthenticationPolicy.ATTEMPT
        self.connector.save()
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["UnlockPolicy"], ["AttemptAuthentication"])

    def test_generate_mdm_macos_grace_period_without_policy(self):
        """Grace periods are omitted when no policy is enforced"""
        self.connector.apple_psso["authentication_method"] = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso["authentication_grace_period"] = 3600
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertNotIn("AuthenticationGracePeriod", psso)

    def test_generate_mdm_macos_exempt_accounts_and_user_creation(self):
        self.connector.apple_psso["authentication_method"] = ApplePSSOAuthenticationMethod.PASSWORD
        self.connector.apple_psso["non_platform_sso_accounts"] = ["breakglass", "localadmin"]
        self.connector.apple_psso["enable_create_user_at_login"] = True
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["NonPlatformSSOAccounts"], ["breakglass", "localadmin"])
        self.assertTrue(psso["EnableCreateUserAtLogin"])

    def test_generate_mdm_macos_password_only_keys_omitted_in_secure_enclave_mode(self):
        """Password-only keys are omitted for the Secure Enclave key method"""
        self.connector.apple_psso["non_platform_sso_accounts"] = ["breakglass"]
        self.connector.apple_psso["enable_create_user_at_login"] = True
        self.connector.apple_psso["authentication_grace_period"] = 3600
        self.connector.apple_psso["offline_grace_period"] = 7200
        self.connector.apple_psso["login_policy"] = ApplePSSOAuthenticationPolicy.REQUIRE
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

    def test_api_apple_psso_defaults(self):
        """A connector with nothing stored is returned with every setting at its default"""
        self.client.force_login(create_test_admin_user())
        res = self.client.get(
            reverse("authentik_api:agentconnector-detail", kwargs={"pk": self.connector.pk})
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.data["apple_psso"]["authentication_method"],
            ApplePSSOAuthenticationMethod.USER_SECURE_ENCLAVE_KEY,
        )
        self.assertEqual(res.data["apple_psso"]["login_frequency"], 64800)
        self.assertEqual(res.data["apple_psso"]["non_platform_sso_accounts"], [])

    def test_api_apple_psso_create(self):
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse("authentik_api:agentconnector-list"),
            data={
                "name": generate_id(),
                "apple_psso": {
                    "authentication_method": ApplePSSOAuthenticationMethod.PASSWORD,
                    "login_policy": ApplePSSOAuthenticationPolicy.REQUIRE,
                },
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        connector = AgentConnector.objects.get(pk=res.data["connector_uuid"])
        self.assertEqual(
            connector.apple_psso_config.authentication_method,
            ApplePSSOAuthenticationMethod.PASSWORD,
        )
        self.assertEqual(
            connector.apple_psso_config.login_policy, ApplePSSOAuthenticationPolicy.REQUIRE
        )

    def test_api_apple_psso_partial_update(self):
        """A partial update keeps the settings that weren't sent"""
        self.connector.apple_psso["biometric_requirement"] = ApplePSSOBiometricRequirement.ANY
        self.connector.save()
        self.client.force_login(create_test_admin_user())
        res = self.client.patch(
            reverse("authentik_api:agentconnector-detail", kwargs={"pk": self.connector.pk}),
            data={"apple_psso": {"login_policy": ApplePSSOAuthenticationPolicy.ATTEMPT}},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.connector.refresh_from_db()
        self.assertEqual(
            self.connector.apple_psso,
            {
                "biometric_requirement": ApplePSSOBiometricRequirement.ANY,
                "login_policy": ApplePSSOAuthenticationPolicy.ATTEMPT,
            },
        )

    def test_api_apple_psso_invalid(self):
        self.client.force_login(create_test_admin_user())
        res = self.client.patch(
            reverse("authentik_api:agentconnector-detail", kwargs={"pk": self.connector.pk}),
            data={"apple_psso": {"login_policy": "sometimes"}},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("login_policy", res.data["apple_psso"])
