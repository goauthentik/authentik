"""Test Controllers"""

import pytest
import yaml
from django.test import TestCase
from structlog.stdlib import get_logger

from authentik.core.tests.utils import create_test_flow
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost, OutpostType
from authentik.outposts.tasks import outpost_connection_discovery
from authentik.providers.proxy.controllers.k8s.ingress import IngressReconciler
from authentik.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from authentik.providers.proxy.models import ProxyMode, ProxyProvider

LOGGER = get_logger()


class TestProxyKubernetes(TestCase):
    """Test Controllers"""

    controller: KubernetesController | None

    def setUp(self):
        # Ensure that local connection have been created
        outpost_connection_discovery.send()
        self.controller = None

    @pytest.mark.timeout(120)
    def test_kubernetes_controller_static(self):
        """Test Kubernetes Controller"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=create_test_flow(),
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

    @pytest.mark.timeout(120)
    def test_kubernetes_controller_ingress(self):
        """Test Kubernetes Controller's Ingress"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="https://localhost",
            authorization_flow=create_test_flow(),
        )
        provider2: ProxyProvider = ProxyProvider.objects.create(
            name="test2",
            internal_host="http://otherhost",
            external_host="https://otherhost",
            mode=ProxyMode.FORWARD_SINGLE,
            authorization_flow=create_test_flow(),
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
