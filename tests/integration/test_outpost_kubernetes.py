"""outpost tests"""
from django.test import TestCase

from authentik.flows.models import Flow
from authentik.lib.config import CONFIG
from authentik.outposts.controllers.k8s.deployment import DeploymentReconciler
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.models import KubernetesServiceConnection, Outpost, OutpostType
from authentik.outposts.tasks import outpost_local_connection
from authentik.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from authentik.providers.proxy.models import ProxyProvider


class OutpostKubernetesTests(TestCase):
    """Test Kubernetes Controllers"""

    def setUp(self):
        super().setUp()
        # Ensure that local connection have been created
        outpost_local_connection()
        self.provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=Flow.objects.first(),
        )
        self.service_connection = KubernetesServiceConnection.objects.first()
        self.outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            service_connection=self.service_connection,
        )
        self.outpost.providers.add(self.provider)
        self.outpost.save()

    def test_deployment_reconciler(self):
        """test that deployment requires update"""
        controller = ProxyKubernetesController(self.outpost, self.service_connection)
        deployment_reconciler = DeploymentReconciler(controller)

        self.assertIsNotNone(deployment_reconciler.retrieve())

        config = self.outpost.config
        config.kubernetes_replicas = 3
        self.outpost.config = config

        with self.assertRaises(NeedsUpdate):
            deployment_reconciler.reconcile(
                deployment_reconciler.retrieve(),
                deployment_reconciler.get_reference_object(),
            )

        with CONFIG.patch("outposts.container_image_base", "test"):
            with self.assertRaises(NeedsUpdate):
                deployment_reconciler.reconcile(
                    deployment_reconciler.retrieve(),
                    deployment_reconciler.get_reference_object(),
                )

        deployment_reconciler.delete(deployment_reconciler.get_reference_object())
