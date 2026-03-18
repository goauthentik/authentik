from cryptography.x509 import (
    Certificate,
    Extension,
    SubjectAlternativeName,
    UniformResourceIdentifier,
)
from rest_framework.exceptions import PermissionDenied

from authentik.crypto.models import CertificateKeyPair, fingerprint_sha256
from authentik.endpoints.models import Device, EndpointStage
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector
from authentik.enterprise.stages.mtls.stage import PLAN_CONTEXT_CERTIFICATE, MTLSStageView
from authentik.flows.planner import PLAN_CONTEXT_DEVICE


class FleetStageView(MTLSStageView):
    def get_authorities(self):
        stage: EndpointStage = self.executor.current_stage
        connector = FleetConnector.objects.filter(pk=stage.connector_id).first()
        controller = connector.controller(connector)
        kp = CertificateKeyPair.objects.filter(managed=controller.mtls_ca_managed).first()
        return [kp] if kp else None

    def lookup_device(self, cert: Certificate):
        san_ext: Extension[SubjectAlternativeName] = cert.extensions.get_extension_for_oid(
            SubjectAlternativeName.oid
        )
        values = san_ext.value.get_values_for_type(UniformResourceIdentifier)
        for v in values:
            self.logger.debug("Looking for device with uuid", fleet_device_uuid=v)
            host = Device.objects.filter().first()
            if not host:
                continue
            self.executor.plan.context[PLAN_CONTEXT_DEVICE] = host
            break
        self.executor.plan.context[PLAN_CONTEXT_CERTIFICATE] = self._cert_to_dict(cert)
        return self.executor.stage_ok()

    def dispatch(self, request, *args, **kwargs):
        stage: EndpointStage = self.executor.current_stage
        try:
            cert = self.get_cert(stage.mode)
        except PermissionDenied as exc:
            return super().dispatch(request, *args, error_message=exc.detail, **kwargs)
        if not cert:
            return self.executor.stage_ok()
        self.logger.debug("Received certificate", cert=fingerprint_sha256(cert))
        return self.lookup_device(cert)
