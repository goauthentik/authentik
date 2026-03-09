from datetime import timedelta
from hmac import compare_digest
from plistlib import PlistFormat, dumps
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from django.http import HttpRequest
from django.urls import reverse
from django.utils.timezone import now
from jwt import PyJWTError, decode, encode
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceToken, EnrollmentToken
from authentik.endpoints.controller import BaseController
from authentik.endpoints.facts import OSFamily
from authentik.endpoints.models import Device
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import JWTAlgorithms


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


class AgentController(BaseController[AgentConnector]):
    @staticmethod
    def vendor_identifier() -> str:
        return "goauthentik.io/platform"

    def supported_enrollment_methods(self):
        return []

    def generate_device_challenge(self):
        keypair = CertificateKeyPair.objects.get(pk=self.connector.challenge_key_id)
        challenge_str = generate_id()
        iat = now()
        challenge = encode(
            {
                "atc": challenge_str,
                "iss": str(self.connector.pk),
                "iat": int(iat.timestamp()),
                "exp": int((iat + timedelta(minutes=5)).timestamp()),
                "goauthentik.io/device/check_in": self.connector.challenge_trigger_check_in,
            },
            headers={"kid": keypair.kid},
            key=keypair.private_key,
            algorithm=JWTAlgorithms.from_private_key(keypair.private_key),
        )
        return challenge

    def validate_device_challenge(self, response: str, challenge: str):
        try:
            raw = decode(
                response,
                options={"verify_signature": False},
                audience="goauthentik.io/platform/endpoint",
            )
        except PyJWTError as exc:
            self.logger.warning("Could not parse response", exc=exc)
            raise ValidationError("Invalid challenge response") from None
        device = Device.filter_not_expired(identifier=raw["iss"]).first()
        if not device:
            self.logger.warning("Could not find device for challenge")
            raise ValidationError("Invalid challenge response")
        for token in DeviceToken.filter_not_expired(
            device__device=device, device__connector=self.connector
        ).values_list("key", flat=True):
            try:
                decoded = decode(
                    response,
                    key=token,
                    algorithms="HS512",
                    issuer=device.identifier,
                    audience="goauthentik.io/platform/endpoint",
                )
                if not compare_digest(decoded["atc"], challenge):
                    self.logger.warning("mismatched challenge")
                    raise ValidationError("Invalid challenge response")
                return device
            except PyJWTError as exc:
                self.logger.warning("failed to validate device challenge response", exc=exc)
        raise ValidationError("Invalid challenge response")

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
                        "URLs": [
                            request.build_absolute_uri(reverse("authentik_core:root-redirect")),
                        ],
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
        return MDMConfigResponseSerializer(
            data={
                "config": payload,
                "mime_type": "application/xml",
                "filename": f"{self.connector.name}_config.mobileconfig",
            }
        )
