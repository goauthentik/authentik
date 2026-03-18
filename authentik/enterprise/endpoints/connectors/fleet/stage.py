from cryptography.x509 import (
    Certificate,
    Extension,
    SubjectAlternativeName,
    UniformResourceIdentifier,
)
from rest_framework.exceptions import PermissionDenied

from authentik.crypto.models import CertificateKeyPair, fingerprint_sha256
from authentik.endpoints.models import Device, EndpointStage, StageMode
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector
from authentik.enterprise.stages.mtls.stage import PLAN_CONTEXT_CERTIFICATE, MTLSStageView
from authentik.flows.planner import PLAN_CONTEXT_DEVICE

FLEET_CONDITIONAL_ACCESS_URI_PREFIX = "urn:device:apple:uuid:"

class FleetStageView(MTLSStageView):
    def get_authorities(self):
        stage: EndpointStage = self.executor.current_stage
        connector = FleetConnector.objects.filter(pk=stage.connector_id).first()
        controller = connector.controller(connector)
        kp = CertificateKeyPair.objects.filter(managed=controller.mtls_ca_managed).first()
        return [kp] if kp else None

    def lookup_device(self, cert: Certificate, mode: StageMode):
        san_ext: Extension[SubjectAlternativeName] = cert.extensions.get_extension_for_oid(
            SubjectAlternativeName.oid
        )
        raw_values = san_ext.value.get_values_for_type(UniformResourceIdentifier)
        values = [x.removeprefix(FLEET_CONDITIONAL_ACCESS_URI_PREFIX).lower() for x in raw_values]
        self.logger.debug("Looking for devices with uuid", fleet_device_uuid=values)
        device = Device.objects.filter(
            **{
                "deviceconnection__devicefactsnapshot__data__vendor__fleetdm.com__uuid__in": values
            }
        ).first()
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
            return super().dispatch(request, *args, error_message=exc.detail, **kwargs)
