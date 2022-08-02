"""Docker controller tests"""
from django.test import TestCase
from docker.models.containers import Container

from authentik.blueprints.tests import reconcile_app
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.controllers.base import ControllerException
from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import DockerServiceConnection, Outpost, OutpostType
from authentik.providers.proxy.controllers.docker import ProxyDockerController


class DockerControllerTests(TestCase):
    """Docker controller tests"""

    @reconcile_app("authentik_outposts")
    def setUp(self) -> None:
        self.outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
        )
        self.integration = DockerServiceConnection(name="test")

    def test_init_managed(self):
        """Docker controller shouldn't do anything for managed outpost"""
        controller = DockerController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(), self.integration
        )
        self.assertIsNone(controller.up())
        self.assertIsNone(controller.down())

    def test_init_invalid(self):
        """Ensure init fails with invalid client"""
        with self.assertRaises(ControllerException):
            DockerController(self.outpost, self.integration)

    def test_env_valid(self):
        """Test environment check"""
        controller = DockerController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(), self.integration
        )
        env = [f"{key}={value}" for key, value in controller._get_env().items()]
        container = Container(attrs={"Config": {"Env": env}})
        self.assertFalse(controller._comp_env(container))

    def test_env_invalid(self):
        """Test environment check"""
        controller = DockerController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(), self.integration
        )
        container = Container(attrs={"Config": {"Env": []}})
        self.assertTrue(controller._comp_env(container))

    def test_label_valid(self):
        """Test label check"""
        controller = DockerController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(), self.integration
        )
        container = Container(attrs={"Config": {"Labels": controller._get_labels()}})
        self.assertFalse(controller._comp_labels(container))

    def test_label_invalid(self):
        """Test label check"""
        controller = DockerController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(), self.integration
        )
        container = Container(attrs={"Config": {"Labels": {}}})
        self.assertTrue(controller._comp_labels(container))
        container = Container(attrs={"Config": {"Labels": {"io.goauthentik.outpost-uuid": "foo"}}})
        self.assertTrue(controller._comp_labels(container))

    def test_port_valid(self):
        """Test port check"""
        controller = ProxyDockerController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(), self.integration
        )
        container = Container(
            attrs={
                "NetworkSettings": {
                    "Ports": {
                        "9000/tcp": [{"HostIp": "", "HostPort": "9000"}],
                        "9443/tcp": [{"HostIp": "", "HostPort": "9443"}],
                    }
                },
                "State": "",
            }
        )
        with self.settings(TEST=False):
            self.assertFalse(controller._comp_ports(container))
            container.attrs["State"] = "running"
            self.assertFalse(controller._comp_ports(container))

    def test_port_invalid(self):
        """Test port check"""
        controller = ProxyDockerController(
            Outpost.objects.filter(managed=MANAGED_OUTPOST).first(), self.integration
        )
        container_no_ports = Container(
            attrs={"NetworkSettings": {"Ports": None}, "State": "running"}
        )
        container_missing_port = Container(
            attrs={
                "NetworkSettings": {
                    "Ports": {
                        "9443/tcp": [{"HostIp": "", "HostPort": "9443"}],
                    }
                },
                "State": "running",
            }
        )
        container_mismatched_host = Container(
            attrs={
                "NetworkSettings": {
                    "Ports": {
                        "9443/tcp": [{"HostIp": "", "HostPort": "123"}],
                    }
                },
                "State": "running",
            }
        )
        with self.settings(TEST=False):
            self.assertFalse(controller._comp_ports(container_no_ports))
            self.assertTrue(controller._comp_ports(container_missing_port))
            self.assertTrue(controller._comp_ports(container_mismatched_host))
