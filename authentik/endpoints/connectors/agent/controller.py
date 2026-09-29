from plistlib import PlistFormat, dumps
from uuid import uuid5
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from django.http import HttpRequest
from django.urls import reverse
from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    ApplePSSOAuthenticationMethod,
    ApplePSSOAuthenticationPolicy,
    EnrollmentToken,
)
from authentik.endpoints.controller import BaseController, Capabilities
from authentik.endpoints.facts import OSFamily


def csp_create_replace_item(loc_uri, data_value) -> Element:
    """Create a Replace/Item element with the specified LocURI and Data"""
    replace = Element("Replace")
    item = SubElement(replace, "Item")

    # Meta section
    meta = SubElement(item, "Meta")
    format_elem = SubElement(meta, "Format")
    format_elem.set("xmlns", "syncml:metinf")
    format_elem.text = "chr"

    # Target section
    target = SubElement(item, "Target")
    loc_uri_elem = SubElement(target, "LocURI")
    loc_uri_elem.text = loc_uri

    # Data section
    data = SubElement(item, "Data")
    data.text = data_value

    return replace


class MDMConfigResponseSerializer(PassiveSerializer):

    config = CharField(required=True)
    mime_type = CharField(required=True)
    filename = CharField(required=True)


class AgentConnectorController(BaseController[AgentConnector]):

    @staticmethod
    def vendor_identifier() -> str:
        return "goauthentik.io/platform"

    def capabilities(self) -> list[Capabilities]:
        return [Capabilities.STAGE_ENDPOINTS]

    def generate_mdm_config(
        self, target_platform: OSFamily, request: HttpRequest, token: EnrollmentToken
    ) -> MDMConfigResponseSerializer:
        response = None
        if target_platform == OSFamily.windows:
            response = self._generate_mdm_config_windows(request, token)
        if target_platform in [OSFamily.iOS, OSFamily.macOS]:
            response = self._generate_mdm_config_macos(request, token)
        if not response:
            raise ValueError(f"Unsupported platform for MDM Configuration: {target_platform}")
        response.is_valid(raise_exception=True)
        return response

    def _generate_mdm_config_windows(
        self, request: HttpRequest, token: EnrollmentToken
    ) -> MDMConfigResponseSerializer:
        base_uri = (
            "./Vendor/MSFT/Registry/HKLM/SOFTWARE/authentik Security Inc./Platform/ManagedConfig"
        )
        token_item = csp_create_replace_item(
            base_uri + "/RegistrationToken",
            token.key,
        )
        url_item = csp_create_replace_item(
            base_uri + "/URL",
            request.build_absolute_uri(reverse("authentik_core:root-redirect")),
        )

        payload = tostring(token_item, encoding="unicode") + tostring(url_item, encoding="unicode")
        return MDMConfigResponseSerializer(
            data={
                "config": payload,
                "mime_type": "application/xml",
                "filename": f"{self.connector.name}_config.csp.xml",
            }
        )

    def _psso_authentication_method(self) -> str:
        return {
            ApplePSSOAuthenticationMethod.PASSWORD: "Password",
            ApplePSSOAuthenticationMethod.USER_SECURE_ENCLAVE_KEY: "UserSecureEnclaveKey",
            ApplePSSOAuthenticationMethod.WEB: "OpenID",
        }[self.connector.apple_psso_config.authentication_method]

    def _psso_login_policies(self) -> dict:
        """Login, unlock and FileVault policies of the Platform SSO payload, which Apple only
        applies to the password method"""
        config = self.connector.apple_psso_config
        if config.authentication_method != ApplePSSOAuthenticationMethod.PASSWORD:
            return {}
        mapping = {
            ApplePSSOAuthenticationPolicy.ATTEMPT: "AttemptAuthentication",
            ApplePSSOAuthenticationPolicy.REQUIRE: "RequireAuthentication",
        }
        modifiers = []
        if config.authentication_grace_period:
            modifiers.append("AllowAuthenticationGracePeriod")
        if config.offline_grace_period:
            modifiers.append("AllowOfflineGracePeriod")
        policies = {}
        for policy, payload_key in (
            (config.login_policy, "LoginPolicy"),
            (config.unlock_policy, "UnlockPolicy"),
            (config.filevault_policy, "FileVaultPolicy"),
        ):
            value = mapping.get(policy)
            if value:
                policies[payload_key] = [value, *modifiers]
                if (
                    payload_key == "UnlockPolicy"
                    and value == "RequireAuthentication"
                    and config.unlock_allow_touch_id_or_watch
                ):
                    policies[payload_key].append("AllowTouchIDOrWatchForUnlock")
        if policies:
            if config.authentication_grace_period:
                policies["AuthenticationGracePeriod"] = config.authentication_grace_period
            if config.offline_grace_period:
                policies["OfflineGracePeriod"] = config.offline_grace_period
        if config.non_platform_sso_accounts:
            policies["NonPlatformSSOAccounts"] = config.non_platform_sso_accounts
        if config.enable_create_user_at_login:
            policies["EnableCreateUserAtLogin"] = True
        return policies

    def _payload_uuid(self, token: EnrollmentToken, payload_type: str) -> str:
        """Stable PayloadUUID, as macOS deregisters Platform SSO when it changes"""
        return str(uuid5(self.connector.pk, f"{token.pk}:{payload_type}"))

    def _generate_mdm_config_macos(
        self, request: HttpRequest, token: EnrollmentToken
    ) -> MDMConfigResponseSerializer:
        token_uuid = str(token.pk).upper()
        payload = dumps(
            {
                "PayloadContent": [
                    # Config for authentik Platform Agent (sysd)
                    {
                        "PayloadDisplayName": "authentik Platform",
                        "PayloadIdentifier": f"io.goauthentik.platform.{token_uuid}",
                        "PayloadType": "io.goauthentik.platform",
                        "PayloadUUID": self._payload_uuid(token, "io.goauthentik.platform"),
                        "PayloadVersion": 1,
                        "RegistrationToken": token.key,
                        "URL": request.build_absolute_uri(reverse("authentik_core:root-redirect")),
                    },
                    # Config for MDM-associated domains (required for PSSO)
                    {
                        "PayloadDisplayName": "Associated Domains",
                        "PayloadIdentifier": f"com.apple.associated-domains.{token_uuid}",
                        "PayloadType": "com.apple.associated-domains",
                        "PayloadUUID": self._payload_uuid(token, "com.apple.associated-domains"),
                        "PayloadVersion": 1,
                        "Configuration": [
                            {
                                "ApplicationIdentifier": "232G855Y8N.io.goauthentik.platform.agent",
                                "AssociatedDomains": [f"authsrv:{request.get_host()}"],
                                "EnableDirectDownloads": False,
                            }
                        ],
                    },
                    # Config for Platform SSO
                    {
                        "PayloadDisplayName": "Platform Single Sign-On",
                        "PayloadIdentifier": f"com.apple.extensiblesso.{token_uuid}",
                        "PayloadType": "com.apple.extensiblesso",
                        "PayloadUUID": self._payload_uuid(token, "com.apple.extensiblesso"),
                        "PayloadVersion": 1,
                        "ExtensionIdentifier": "io.goauthentik.platform.psso",
                        "TeamIdentifier": "232G855Y8N",
                        "Type": "Redirect",
                        "URLs": [
                            request.build_absolute_uri(reverse("authentik_core:root-redirect")),
                        ],
                        "PlatformSSO": {
                            "AccountDisplayName": "authentik",
                            "AllowDeviceIdentifiersInAttestation": True,
                            "AuthenticationMethod": self._psso_authentication_method(),
                            "EnableAuthorization": True,
                            "UseSharedDeviceKeys": True,
                            "LoginFrequency": self.connector.apple_psso_config.login_frequency,
                            **self._psso_login_policies(),
                        },
                    },
                ],
                "PayloadDisplayName": "authentik Platform",
                "PayloadIdentifier": str(self.connector.pk).upper(),
                "PayloadScope": "System",
                "PayloadType": "Configuration",
                "PayloadUUID": str(self.connector.pk).upper(),
                "PayloadVersion": 1,
            },
            fmt=PlistFormat.FMT_XML,
        ).decode()
        return MDMConfigResponseSerializer(
            data={
                "config": payload,
                "mime_type": "application/xml",
                "filename": f"{self.connector.name}_config.mobileconfig",
            }
        )
