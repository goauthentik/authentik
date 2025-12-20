from json import dumps, loads

from django.http import HttpResponseRedirect
from django.urls import reverse
from googleapiclient.discovery import build

from authentik.endpoints.controller import BaseController, EnrollmentMethods
from authentik.endpoints.facts import DeviceFacts, OSFamily
from authentik.endpoints.models import Device, DeviceConnection
from authentik.enterprise.endpoints.connectors.google_chrome.google_schema import (
    DeviceSignals,
    VerifyChallengeResponseResult,
)
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.policies.utils import delete_none_values

# Header we get from chrome that initiates verified access
HEADER_DEVICE_TRUST = "X-Device-Trust"
# Header we send to the client with the challenge
HEADER_ACCESS_CHALLENGE = "X-Verified-Access-Challenge"
# Header we get back from the client that we verify with google
HEADER_ACCESS_CHALLENGE_RESPONSE = "X-Verified-Access-Challenge-Response"
# Header value for x-device-trust that initiates the flow
DEVICE_TRUST_VERIFIED_ACCESS = "VerifiedAccess"


class GoogleChromeController(BaseController[GoogleChromeConnector]):

    def __init__(self, connector):
        super().__init__(connector)
        self.google_client = build(
            "verifiedaccess",
            "v2",
            cache_discovery=False,
            **connector.google_credentials(),
        )

    def supported_enrollment_methods(self) -> list[EnrollmentMethods]:
        return [EnrollmentMethods.AUTOMATIC_USER]

    def generate_challenge(self) -> HttpResponseRedirect:
        challenge = self.google_client.challenge().generate().execute()
        res = HttpResponseRedirect(
            self.request.build_absolute_uri(
                reverse("authentik_endpoints_connectors_google_chrome:chrome")
            )
        )
        res[HEADER_ACCESS_CHALLENGE] = dumps(challenge)
        return res

    def validate_challenge(self, response: str):
        response = VerifyChallengeResponseResult(
            self.google_client.challenge().verify(body=loads(response)).execute()
        )
        # Remove deprecated string representation of deviceSignals
        response.pop("deviceSignal", None)
        signals = DeviceSignals(response["deviceSignals"])
        device, _ = Device.objects.update_or_create(
            identifier=signals["serialNumber"],
            defaults={
                "name": signals["hostname"],
            },
        )
        conn, _ = DeviceConnection.objects.update_or_create(
            device=device,
            connector=self.connector,
        )
        conn.create_snapshot(self.convert_data(signals))

    def convert_os_family(self, family) -> OSFamily:
        match family:
            case "CHROME_OS":
                return OSFamily.linux
            case "CHROMIUM_OS":
                return OSFamily.linux
            case "WINDOWS":
                return OSFamily.windows
            case "MAC_OS_X":
                return OSFamily.macOS
            case "LINUX":
                return OSFamily.linux
        return OSFamily.other

    def convert_data(self, raw_signals: DeviceSignals):
        data = {
            "os": delete_none_values(
                {
                    "family": self.convert_os_family(raw_signals["operatingSystem"]),
                    "version": raw_signals["osVersion"],
                }
            ),
            "disks": [],
            "network": delete_none_values(
                {
                    "hostname": raw_signals["hostname"],
                    "interfaces": [],
                    "firewall_enabled": raw_signals["osFirewall"] == "OS_FIREWALL_ENABLED",
                },
            ),
            "hardware": delete_none_values(
                {
                    "model": raw_signals["deviceModel"],
                    "manufacturer": raw_signals["deviceManufacturer"],
                    "serial": raw_signals["serialNumber"],
                }
            ),
            "vendor": {
                "chrome.google.com": {
                    "agent_version": raw_signals["browserVersion"],
                    "raw": raw_signals,
                },
            },
        }
        facts = DeviceFacts(data=data)
        facts.is_valid(raise_exception=True)
        return facts.validated_data
