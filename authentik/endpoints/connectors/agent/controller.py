from plistlib import PlistFormat, dumps
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from django.http import HttpRequest
from django.urls import reverse

from authentik.endpoints.connectors.agent.models import AgentConnector, EnrollmentToken
from authentik.endpoints.controller import BaseController
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


class AgentConnectorController(BaseController[AgentConnector]):

    def supported_enrollment_methods(self):
        return []

    def generate_mdm_config(
        self, target_platform: OSFamily, request: HttpRequest, token: EnrollmentToken
    ) -> str:
        if target_platform == OSFamily.windows:
            return self._generate_mdm_config_windows(request, token)
        if target_platform in [OSFamily.iOS, OSFamily.macOS]:
            return self._generate_mdm_config_macos(request, token)
        raise ValueError(f"Unsupported platform for MDM Configuration: {target_platform}")

    def _generate_mdm_config_windows(self, request: HttpRequest, token: EnrollmentToken) -> str:
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
        return payload

    def _generate_mdm_config_macos(self, request: HttpRequest, token: EnrollmentToken) -> str:
        token_uuid = str(token.pk).upper()
        payload = dumps(
            {
                "PayloadContent": [
                    # Config for authentik Platform Agent (sysd)
                    {
                        "PayloadDisplayName": "authentik Platform",
                        "PayloadIdentifier": f"io.goauthentik.platform.{token_uuid}",
                        "PayloadType": "io.goauthentik.platform",
                        "PayloadUUID": str(uuid4()),
                        "PayloadVersion": 1,
                        "RegistrationToken": token.key,
                        "URL": request.build_absolute_uri(reverse("authentik_core:root-redirect")),
                    },
                    # Config for MDM-associated domains (required for PSSO)
                    {
                        "PayloadDisplayName": "Associated Domains",
                        "PayloadIdentifier": f"com.apple.associated-domains.{token_uuid}",
                        "PayloadType": "com.apple.associated-domains",
                        "PayloadUUID": str(uuid4()),
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
                        "PayloadUUID": str(uuid4()),
                        "PayloadVersion": 1,
                        "ExtensionIdentifier": "io.goauthentik.platform.psso",
                        "TeamIdentifier": "232G855Y8N",
                        "Type": "Redirect",
                        "URLs": [request.build_absolute_uri("")],
                        "PlatformSSO": {
                            "AccountDisplayName": "authentik",
                            "AllowDeviceIdentifiersInAttestation": True,
                            "AuthenticationMethod": "UserSecureEnclaveKey",
                            "EnableAuthorization": True,
                            "EnableCreateUserAtLogin": True,
                            "FileVaultPolicy": ["RequireAuthentication"],
                            "LoginPolicy": ["RequireAuthentication"],
                            "NewUserAuthorizationMode": "Standard",
                            "UnlockPolicy": ["RequireAuthentication"],
                            "UseSharedDeviceKeys": True,
                            "UserAuthorizationMode": "Standard",
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
        return payload
