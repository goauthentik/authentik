from cryptography.x509 import (
    Certificate,
    ExtensionNotFound,
    NameOID,
    SubjectAlternativeName,
    UniformResourceIdentifier,
)
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from authentik.brands.models import Brand
from authentik.crypto.models import CertificateKeyPair, fingerprint_sha256
from authentik.endpoints.models import Device, EndpointStage, StageMode
from authentik.enterprise.stages.mtls.stage import PLAN_CONTEXT_CERTIFICATE, MTLSStageView
from authentik.flows.planner import PLAN_CONTEXT_DEVICE

# Cisco ISE's `ID:<vendor>:GUID:<id>` SAN URI scheme, which is commonly used in Intune SCEP/PKCS
# profiles, either as `ID:Intune:GUID:{{DeviceId}}` or
# `ID:Microsoft Endpoint Manager:GUID:{{DeviceId}}`
# https://www.cisco.com/c/en/us/td/docs/security/ise/UEM-MDM-Server-Integration/b_MDM_UEM_Servers_CiscoISE.pdf
# (chapter "Integrate Microsoft Endpoint Manager Intune")
# https://community.cisco.com/t5/network-access-control/integrating-ise-with-azure-intune-as-mdm/m-p/4686559
GUID_URI_MARKER = "GUID:"
VENDOR_PREFIX = "deviceconnection__devicefactsnapshot__data__vendor__intune.microsoft.com"


class MicrosoftIntuneStageView(MTLSStageView):
    def get_authorities(self):
        # Intune certificates are issued by the customer's CA (Cloud PKI, ADCS/NDES, etc),
        # which is configured on the connector, falling back to the brand's client certificates
        stage: EndpointStage = self.executor.current_stage
        cas = CertificateKeyPair.objects.filter(microsoftintuneconnector=stage.connector_id)
        if cas.exists():
            return cas.order_by("name")
        brand: Brand = self.request.brand
        if brand.client_certificates.exists():
            return brand.client_certificates.order_by("name")
        return None

    def get_device_ids(self, cert: Certificate) -> list[str]:
        """Collect candidate device IDs from the certificate's CN and SAN URIs.
        Intune profiles set these with `{{DeviceId}}` (Intune device ID) or
        `{{AAD_Device_ID}}`/`{{AzureADDeviceId}}` (Entra device ID), see "Subject name format"
        https://learn.microsoft.com/en-us/intune/device-configuration/certificates/scep-profiles"""
        values = [x.value for x in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)]
        try:
            san_ext = cert.extensions.get_extension_for_class(SubjectAlternativeName)
            values.extend(san_ext.value.get_values_for_type(UniformResourceIdentifier))
        except ExtensionNotFound:
            # SAN is optional; fall back to CN-derived identifiers only.
            pass
        return [str(x).rpartition(GUID_URI_MARKER)[2].lower() for x in values]

    def lookup_device(self, cert: Certificate, mode: StageMode):
        stage: EndpointStage = self.executor.current_stage
        values = self.get_device_ids(cert)
        self.logger.debug("Looking for devices with ID", intune_device_id=values)
        # `id` is the Intune device ID and `azureADDeviceId` the Entra device ID, see
        # https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-manageddevice?view=graph-rest-1.0
        device = (
            Device.objects.filter(deviceconnection__connector=stage.connector_id)
            .filter(
                Q(**{f"{VENDOR_PREFIX}__id__in": values})
                | Q(**{f"{VENDOR_PREFIX}__azure_a_d_device_id__in": values})
            )
            .first()
        )
        if not device and mode == StageMode.REQUIRED:
            raise PermissionDenied("Failed to find device")
        self.executor.plan.context[PLAN_CONTEXT_DEVICE] = device
        self.executor.plan.context[PLAN_CONTEXT_CERTIFICATE] = self._cert_to_dict(cert)
        return self.executor.stage_ok()

    def dispatch(self, request, *args, **kwargs):
        stage: EndpointStage = self.executor.current_stage
        try:
            cert = self.get_cert(stage.mode)
            if not cert:
                return self.executor.stage_ok()
            self.logger.debug("Received certificate", cert=fingerprint_sha256(cert))
            return self.lookup_device(cert, stage.mode)
        except PermissionDenied as exc:
            return self.executor.stage_invalid(error_message=exc.detail)
