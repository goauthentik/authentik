from plistlib import PlistFormat, dumps
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
        payload = dumps(
            {
                "PayloadContent": [
                    {
                        "PayloadDisplayName": "authentik Platform",
                        "PayloadIdentifier": f"io.goauthentik.platform.{str(token.pk).upper()}",
                        "PayloadType": "io.goauthentik.platform",
                        "PayloadUUID": str(token.pk).upper(),
                        "PayloadVersion": 1,
                        "RegistrationToken": token.key,
                        "URL": request.build_absolute_uri(reverse("authentik_core:root-redirect")),
                    }
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
