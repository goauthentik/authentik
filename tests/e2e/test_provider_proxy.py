"""Proxy and Outpost e2e tests"""
from dataclasses import asdict
from sys import platform
from time import sleep
from typing import Any, Dict, Optional
from unittest.case import skipUnless

from channels.testing import ChannelsLiveServerTestCase
from docker.client import DockerClient, from_env
from docker.models.containers import Container
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from authentik import __version__
from authentik.core.models import Application
from authentik.flows.models import Flow
from authentik.outposts.apps import AuthentikOutpostConfig
from authentik.outposts.models import (
    DockerServiceConnection,
    Outpost,
    OutpostConfig,
    OutpostType,
)
from authentik.providers.proxy.models import ProxyProvider
from tests.e2e.utils import USER, SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderProxy(SeleniumTestCase):
    """Proxy and Outpost e2e tests"""

    proxy_container: Container

    def tearDown(self) -> None:
        super().tearDown()
        self.proxy_container.kill()

    def get_container_specs(self) -> Optional[Dict[str, Any]]:
        return {
            "image": "docker.beryju.org/proxy/traefik/whoami:latest",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
        }

    def start_proxy(self, outpost: Outpost) -> Container:
        """Start proxy container based on outpost created"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image=f"docker.beryju.org/proxy/beryju/authentik-proxy:{__version__}",
            detach=True,
            network_mode="host",
            # auto_remove=True,
            environment={
                "AUTHENTIK_HOST": self.live_server_url,
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
        )
        return container

    @retry()
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
        )
        outpost.providers.add(proxy)
        outpost.save()

        self.proxy_container = self.start_proxy(outpost)

        # Wait until outpost healthcheck succeeds
        healthcheck_retries = 0
        while healthcheck_retries < 50:
            if len(outpost.state) > 0:
                state = outpost.state[0]
                if state.last_seen:
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
        self.assertIn("X-Forwarded-Preferred-Username: akadmin", full_body_text)


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderProxyConnect(ChannelsLiveServerTestCase):
    """Test Proxy connectivity over websockets"""

    @retry()
    def test_proxy_connectivity(self):
        """Test proxy connectivity over websocket"""
        AuthentikOutpostConfig.init_local_connection()
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
        service_connection = DockerServiceConnection.objects.get(local=True)
        outpost: Outpost = Outpost.objects.create(
            name="proxy_outpost",
            type=OutpostType.PROXY,
            service_connection=service_connection,
            _config=asdict(
                OutpostConfig(authentik_host=self.live_server_url, log_level="debug")
            ),
        )
        outpost.providers.add(proxy)
        outpost.save()

        # Wait until outpost healthcheck succeeds
        healthcheck_retries = 0
        while healthcheck_retries < 50:
            if len(outpost.state) > 0:
                state = outpost.state[0]
                if state.last_seen and state.version:
                    break
            healthcheck_retries += 1
            sleep(0.5)

        state = outpost.state
        self.assertEqual(len(state), 1)
        self.assertEqual(state[0].version, __version__)

        # Make sure to delete the outpost to remove the container
        outpost.delete()
