"""Test Controllers"""
import yaml
from django.test import TestCase

from authentik.flows.models import Flow
from authentik.outposts.apps import AuthentikOutpostConfig
from authentik.outposts.models import KubernetesServiceConnection, Outpost, OutpostType
from authentik.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from authentik.providers.proxy.models import ProxyProvider


class TestControllers(TestCase):
    """Test Controllers"""

    def setUp(self):
        # Ensure that local connection have been created
        AuthentikOutpostConfig.init_local_connection()

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

        controller = ProxyKubernetesController(outpost, service_connection)
        manifest = controller.get_static_deployment()
        self.assertEqual(len(list(yaml.load_all(manifest, Loader=yaml.SafeLoader))), 4)

    def test_kubernetes_controller_deploy(self):
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

        controller = ProxyKubernetesController(outpost, service_connection)
        controller.up()
        controller.down()
