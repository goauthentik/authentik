from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus

from django.urls import reverse
from guardian.shortcuts import assign_perm

from authentik.core.models import User
from authentik.core.tests.utils import (
    create_test_brand,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.stages.mtls.models import (
    CertAttributes,
    MutualTLSStage,
    TLSMode,
    UserAttributes,
)
from authentik.enterprise.stages.mtls.stage import PLAN_CONTEXT_CERTIFICATE
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.outposts.models import Outpost, OutpostType
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class MTLSStageTests(FlowTestCase):

    def setUp(self):
        super().setUp()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.ca = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=load_fixture("fixtures/ca.pem"),
        )
        self.stage = MutualTLSStage.objects.create(
            name=generate_id(),
            mode=TLSMode.REQUIRED,
            cert_attribute=CertAttributes.COMMON_NAME,
            user_attribute=UserAttributes.USERNAME,
        )

        self.stage.certificate_authorities.add(self.ca)
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)
        self.client_cert = load_fixture("fixtures/cert_client.pem")
        # User matching the certificate
        User.objects.filter(username="client").delete()
        self.cert_user = create_test_user(username="client")

    def test_parse_xfcc(self):
        """Test authentik Proxy/Envoy's XFCC format"""
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Forwarded-Client-Cert": f"Cert={quote_plus(self.client_cert)}"},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        self.assertEqual(plan().context[PLAN_CONTEXT_PENDING_USER], self.cert_user)

    def test_parse_nginx(self):
        """Test nginx's format"""
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"SSL-Client-Cert": quote_plus(self.client_cert)},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        self.assertEqual(plan().context[PLAN_CONTEXT_PENDING_USER], self.cert_user)

    def test_parse_traefik(self):
        """Test traefik's format"""
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Forwarded-TLS-Client-Cert": quote_plus(self.client_cert)},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        self.assertEqual(plan().context[PLAN_CONTEXT_PENDING_USER], self.cert_user)

    def test_parse_outpost_object(self):
        """Test outposts's format"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.PROXY)
        assign_perm("pass_outpost_certificate", outpost.user, self.stage)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=outpost.user),
        ):
            with self.assertFlowFinishes() as plan:
                res = self.client.get(
                    reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                    headers={"X-Authentik-Outpost-Certificate": quote_plus(self.client_cert)},
                )
                self.assertEqual(res.status_code, 200)
                self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
            self.assertEqual(plan().context[PLAN_CONTEXT_PENDING_USER], self.cert_user)

    def test_parse_outpost_global(self):
        """Test outposts's format"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.PROXY)
        assign_perm("authentik_stages_mtls.pass_outpost_certificate", outpost.user)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=outpost.user),
        ):
            with self.assertFlowFinishes() as plan:
                res = self.client.get(
                    reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                    headers={"X-Authentik-Outpost-Certificate": quote_plus(self.client_cert)},
                )
                self.assertEqual(res.status_code, 200)
                self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
            self.assertEqual(plan().context[PLAN_CONTEXT_PENDING_USER], self.cert_user)

    def test_parse_outpost_no_perm(self):
        """Test outposts's format"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.PROXY)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=outpost.user),
        ):
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Authentik-Outpost-Certificate": quote_plus(self.client_cert)},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageResponse(res, self.flow, component="ak-stage-access-denied")

    def test_invalid_cert(self):
        """Test invalid certificate"""
        cert = create_test_cert()
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Forwarded-TLS-Client-Cert": quote_plus(cert.certificate_data)},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageResponse(res, self.flow, component="ak-stage-access-denied")
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER, plan().context)

    def test_auth_no_user(self):
        """Test auth with no user"""
        User.objects.filter(username="client").delete()
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            headers={"X-Forwarded-TLS-Client-Cert": quote_plus(self.client_cert)},
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, self.flow, component="ak-stage-access-denied")

    def test_brand_ca(self):
        """Test using a CA from the brand"""
        self.stage.certificate_authorities.clear()

        brand = create_test_brand()
        brand.client_certificates.add(self.ca)
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Forwarded-TLS-Client-Cert": quote_plus(self.client_cert)},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        self.assertEqual(plan().context[PLAN_CONTEXT_PENDING_USER], self.cert_user)

    def test_no_ca_optional(self):
        """Test using no CA Set"""
        self.stage.mode = TLSMode.OPTIONAL
        self.stage.certificate_authorities.clear()
        self.stage.save()
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            headers={"X-Forwarded-TLS-Client-Cert": quote_plus(self.client_cert)},
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))

    def test_no_ca_required(self):
        """Test using no CA Set"""
        self.stage.certificate_authorities.clear()
        self.stage.save()
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            headers={"X-Forwarded-TLS-Client-Cert": quote_plus(self.client_cert)},
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, self.flow, component="ak-stage-access-denied")

    def test_no_cert_optional(self):
        """Test using no cert Set"""
        self.stage.mode = TLSMode.OPTIONAL
        self.stage.save()
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))

    def test_enroll(self):
        """Test Enrollment flow"""
        self.flow.designation = FlowDesignation.ENROLLMENT
        self.flow.save()
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Forwarded-TLS-Client-Cert": quote_plus(self.client_cert)},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        self.assertEqual(plan().context[PLAN_CONTEXT_PROMPT], {"email": None, "name": "client"})
        self.assertEqual(
            plan().context[PLAN_CONTEXT_CERTIFICATE],
            {
                "fingerprint_sha1": "52:39:ca:1e:3a:1f:78:3a:9f:26:3b:c2:84:99:48:68:99:99:81:8a",
                "fingerprint_sha256": (
                    "c1:07:8b:7c:e9:02:57:87:1e:92:e5:81:83:21:bc:92:c7:47:65:e3:97:fb:05:97:6f:36:9e:b5:31:77:98:b7"
                ),
                "issuer": "OU=Self-signed,O=authentik,CN=authentik Test CA",
                "serial_number": "70153443448884702681996102271549704759327537151",
                "subject": "CN=client",
            },
        )
