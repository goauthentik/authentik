"""Test Controllers"""
from os import environ
from unittest import skipUnless

import yaml
from django.test import TestCase

from passbook.flows.models import Flow
from passbook.outposts.models import Outpost, OutpostDeploymentType, OutpostType
from passbook.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from passbook.providers.proxy.models import ProxyProvider


@skipUnless("PB_TEST_K8S" in environ, "Kubernetes test cluster required")
class TestControllers(TestCase):
    """Test Controllers"""

    def test_kubernetes_controller_static(self):
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
            deployment_type=OutpostDeploymentType.KUBERNETES,
        )
        outpost.providers.add(provider)
        outpost.save()

        controller = ProxyKubernetesController(outpost)
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
        outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            deployment_type=OutpostDeploymentType.KUBERNETES,
        )
        outpost.providers.add(provider)
        outpost.save()

        controller = ProxyKubernetesController(outpost)
        controller.up()
        controller.down()
