"""Proxy and Outpost e2e tests"""
from sys import platform
from time import sleep
from typing import Any, Dict, Optional
from unittest.case import skipUnless

from channels.testing import ChannelsLiveServerTestCase
from docker.client import DockerClient, from_env
from docker.models.containers import Container
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from e2e.utils import USER, SeleniumTestCase
from passbook import __version__
from passbook.core.models import Application
from passbook.flows.models import Flow
from passbook.outposts.models import Outpost, OutpostDeploymentType, OutpostType
from passbook.providers.proxy.models import ProxyProvider


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderProxy(SeleniumTestCase):
    """Proxy and Outpost e2e tests"""

    proxy_container: Container

    def tearDown(self) -> None:
        super().tearDown()
        self.proxy_container.kill()

    def get_container_specs(self) -> Optional[Dict[str, Any]]:
        return {
            "image": "traefik/whoami:latest",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
        }

    def start_proxy(self, outpost: Outpost) -> Container:
        """Start proxy container based on outpost created"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="beryju/passbook-proxy:latest",
            detach=True,
            network_mode="host",
            auto_remove=True,
            environment={
                "PASSBOOK_HOST": self.live_server_url,
                "PASSBOOK_TOKEN": outpost.token.token_uuid.hex,
            },
        )
        return container

    def test_proxy_simple(self):
        """Test simple outpost setup with single provider"""
        proxy: ProxyProvider = ProxyProvider.objects.create(
            name="proxy_provider",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            internal_host="http://localhost:80",
            external_host="http://localhost:4180",
        )
        # Ensure OAuth2 Params are set
        proxy.set_oauth_defaults()
        proxy.save()
        # we need to create an application to actually access the proxy
        Application.objects.create(name="proxy", slug="proxy", provider=proxy)
        outpost: Outpost = Outpost.objects.create(
            name="proxy_outpost",
            type=OutpostType.PROXY,
            deployment_type=OutpostDeploymentType.CUSTOM,
        )
        outpost.providers.add(proxy)
        outpost.save()

        self.proxy_container = self.start_proxy(outpost)

        # Wait until outpost healthcheck succeeds
        healthcheck_retries = 0
        while healthcheck_retries < 50:
            if outpost.deployment_health:
                break
            healthcheck_retries += 1
            sleep(0.5)

        self.driver.get("http://localhost:4180")

        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        self.assertIn("X-Forwarded-Preferred-Username: pbadmin", full_body_text)


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderProxyConnect(ChannelsLiveServerTestCase):
    """Test Proxy connectivity over websockets"""

    proxy_container: Container

    def tearDown(self) -> None:
        self.proxy_container.kill()
        super().tearDown()

    def start_proxy(self, outpost: Outpost) -> Container:
        """Start proxy container based on outpost created"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="beryju/passbook-proxy:latest",
            detach=True,
            network_mode="host",
            auto_remove=True,
            environment={
                "PASSBOOK_HOST": self.live_server_url,
                "PASSBOOK_TOKEN": outpost.token.token_uuid.hex,
            },
        )
        return container

    def test_proxy_connectivity(self):
        """Test proxy connectivity over websocket"""
        SeleniumTestCase().apply_default_data()
        proxy: ProxyProvider = ProxyProvider.objects.create(
            name="proxy_provider",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            internal_host="http://localhost:80",
            external_host="http://localhost:4180",
        )
        # Ensure OAuth2 Params are set
        proxy.set_oauth_defaults()
        proxy.save()
        # we need to create an application to actually access the proxy
        Application.objects.create(name="proxy", slug="proxy", provider=proxy)
        outpost: Outpost = Outpost.objects.create(
            name="proxy_outpost",
            type=OutpostType.PROXY,
            deployment_type=OutpostDeploymentType.CUSTOM,
        )
        outpost.providers.add(proxy)
        outpost.save()

        self.proxy_container = self.start_proxy(outpost)

        # Wait until outpost healthcheck succeeds
        healthcheck_retries = 0
        while healthcheck_retries < 50:
            if outpost.deployment_health:
                break
            healthcheck_retries += 1
            sleep(0.5)

        self.assertIsNotNone(outpost.deployment_health)
        self.assertEqual(outpost.deployment_version.get("version"), __version__)
