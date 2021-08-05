"""Test Controllers"""
from typing import Optional

import yaml
from django.test import TestCase
from structlog.stdlib import get_logger

from authentik.flows.models import Flow
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost, OutpostType
from authentik.outposts.tasks import outpost_local_connection
from authentik.providers.proxy.controllers.k8s.ingress import IngressReconciler
from authentik.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from authentik.providers.proxy.models import ProxyMode, ProxyProvider

LOGGER = get_logger()


class TestProxyKubernetes(TestCase):
    """Test Controllers"""

    controller: Optional[KubernetesController]

    def setUp(self):
        # Ensure that local connection have been created
        outpost_local_connection()
        self.controller = None

    def tearDown(self) -> None:
        if self.controller:
            for log in self.controller.down_with_logs():
                LOGGER.info(log)
        return super().tearDown()

    def test_kubernetes_controller_static(self):
        """Test Kubernetes Controller"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=Flow.objects.first(),
        )
        service_connection = KubernetesServiceConnection.objects.first()
        outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            service_connection=service_connection,
        )
        outpost.providers.add(provider)
        outpost.save()

        self.controller = ProxyKubernetesController(outpost, service_connection)
        manifest = self.controller.get_static_deployment()
        self.assertEqual(len(list(yaml.load_all(manifest, Loader=yaml.SafeLoader))), 4)

    def test_kubernetes_controller_ingress(self):
        """Test Kubernetes Controller's Ingress"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="https://localhost",
            authorization_flow=Flow.objects.first(),
        )
        provider2: ProxyProvider = ProxyProvider.objects.create(
            name="test2",
            internal_host="http://otherhost",
            external_host="https://otherhost",
            mode=ProxyMode.FORWARD_SINGLE,
            authorization_flow=Flow.objects.first(),
        )

        service_connection = KubernetesServiceConnection.objects.first()
        outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            service_connection=service_connection,
        )
        outpost.providers.add(provider)

        self.controller = ProxyKubernetesController(outpost, service_connection)

        ingress_rec = IngressReconciler(self.controller)
        ingress = ingress_rec.retrieve()

        self.assertEqual(len(ingress.spec.rules), 1)
        self.assertEqual(ingress.spec.rules[0].host, "localhost")

        # add provider, check again
        outpost.providers.add(provider2)
        ingress = ingress_rec.retrieve()

        self.assertEqual(len(ingress.spec.rules), 2)
        self.assertEqual(ingress.spec.rules[0].host, "localhost")
        self.assertEqual(ingress.spec.rules[1].host, "otherhost")
