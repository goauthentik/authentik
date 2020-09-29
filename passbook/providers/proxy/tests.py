"""Test Controllers"""
import yaml
from django.test import TestCase

from passbook.flows.models import Flow
from passbook.outposts.models import Outpost, OutpostDeploymentType, OutpostType
from passbook.providers.proxy.controllers.kubernetes import KubernetesController
from passbook.providers.proxy.models import ProxyProvider


class TestControllers(TestCase):
    """Test Controllers"""

    def test_kubernetes_controller(self):
        """Test Kubernetes Controller"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=Flow.objects.first(),
        )
        outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            deployment_type=OutpostDeploymentType.CUSTOM,
        )
        outpost.providers.add(provider)
        outpost.save()

        controller = KubernetesController(outpost.pk)
        manifest = controller.get_static_deployment()
        self.assertEqual(len(list(yaml.load_all(manifest, Loader=yaml.SafeLoader))), 3)
