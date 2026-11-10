from datetime import timedelta
from json import loads
from unittest.mock import MagicMock, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from django.urls import reverse
from django.utils.timezone import now
from kiota_serialization_json.json_parse_node import JsonParseNode
from msgraph.generated.models.managed_device import ManagedDevice

from authentik.brands.models import Brand
from authentik.core.tests.utils import create_test_brand, create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.models import Device, DeviceConnection, EndpointStage, StageMode
from authentik.enterprise.endpoints.connectors.microsoft_intune.controller import (
    MicrosoftIntuneController,
)
from authentik.enterprise.endpoints.connectors.microsoft_intune.models import (
    MicrosoftIntuneConnector,
)
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture

TEST_HOST = loads(load_fixture("fixtures/device.json"))
INTUNE_DEVICE_ID = TEST_HOST["value"][0]["id"]


def _name(cn: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])


@patch(
    "authentik.enterprise.endpoints.connectors.microsoft_intune.models.MicrosoftIntuneConnector.microsoft_credentials",
    MagicMock(return_value={}),
)
class TestIntuneStage(FlowTestCase):
    def setUp(self):
        super().setUp()
        self.connector = MicrosoftIntuneConnector.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            tenant_id=generate_id(),
        )
        device = JsonParseNode(TEST_HOST["value"][0]).get_object_value(ManagedDevice)
        self.device = Device.objects.create(identifier=generate_id(), name=generate_id())
        DeviceConnection.objects.create(
            device=self.device, connector=self.connector
        ).create_snapshot(MicrosoftIntuneController(self.connector).map_device_data(device))

        # CA + device certificate as issued by an Intune SCEP/PKCS profile
        ca_key = ec.generate_private_key(ec.SECP256R1())
        self.ca = (
            x509.CertificateBuilder()
            .subject_name(_name("Intune test CA"))
            .issuer_name(_name("Intune test CA"))
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now() - timedelta(days=1))
            .not_valid_after(now() + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False
            )
            .sign(ca_key, hashes.SHA256())
        )
        dev_key = ec.generate_private_key(ec.SECP256R1())
        self.cert = (
            x509.CertificateBuilder()
            .subject_name(_name(generate_id()))
            .issuer_name(self.ca.subject)
            .public_key(dev_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now() - timedelta(days=1))
            .not_valid_after(now() + timedelta(days=1))
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.UniformResourceIdentifier(f"ID:Intune:GUID:{INTUNE_DEVICE_ID}")]
                ),
                critical=False,
            )
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )

        self.kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=self.ca.public_bytes(serialization.Encoding.PEM).decode(),
        )
        self.connector.certificate_authorities.add(self.kp)

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = EndpointStage.objects.create(
            name=generate_id(), mode=StageMode.REQUIRED, connector=self.connector
        )
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)

    def _get(self):
        pem = self.cert.public_bytes(serialization.Encoding.PEM).decode()
        return self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            headers={"X-Forwarded-TLS-Client-Cert": "".join(pem.splitlines()[1:-1])},
        )

    def test_assoc(self):
        with self.assertFlowFinishes() as plan:
            self.assertEqual(self._get().status_code, 200)
        self.assertEqual(plan().context[PLAN_CONTEXT_DEVICE], self.device)

    def test_assoc_not_found(self):
        self.device.delete()
        with self.assertFlowFinishes() as plan:
            res = self._get()
            self.assertStageResponse(res, self.flow, component="ak-stage-access-denied")
        self.assertNotIn(PLAN_CONTEXT_DEVICE, plan().context)

    def test_assoc_brand_ca(self):
        self.connector.certificate_authorities.clear()
        Brand.objects.all().delete()
        create_test_brand().client_certificates.add(self.kp)
        with self.assertFlowFinishes() as plan:
            self.assertEqual(self._get().status_code, 200)
        self.assertEqual(plan().context[PLAN_CONTEXT_DEVICE], self.device)

    def test_no_ca(self):
        self.connector.certificate_authorities.clear()
        Brand.objects.all().delete()
        create_test_brand()
        with self.assertFlowFinishes() as plan:
            res = self._get()
            self.assertStageResponse(res, self.flow, component="ak-stage-access-denied")
        self.assertNotIn(PLAN_CONTEXT_DEVICE, plan().context)
