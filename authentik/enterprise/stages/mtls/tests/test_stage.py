from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus

from django.urls import reverse
from guardian.shortcuts import assign_perm

from authentik.core.models import User
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.stages.mtls.models import (
    CertAttributes,
    MutualTLSStage,
    TLSMode,
    UserAttributes,
)
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.outposts.models import Outpost, OutpostType


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
            certificate_authority=self.ca,
            mode=TLSMode.REQUIRED,
            cert_attribute=CertAttributes.COMMON_NAME,
            user_attribute=UserAttributes.USERNAME,
        )
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
        # Test object permission
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
        # Test global permission
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
