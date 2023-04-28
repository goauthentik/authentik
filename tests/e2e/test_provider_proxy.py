"""Proxy and Outpost e2e tests"""
from base64 import b64encode
from dataclasses import asdict
from sys import platform
from time import sleep
from typing import Any, Optional
from unittest.case import skipUnless

from channels.testing import ChannelsLiveServerTestCase
from docker.client import DockerClient, from_env
from docker.models.containers import Container
from selenium.webdriver.common.by import By

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import DockerServiceConnection, Outpost, OutpostConfig, OutpostType
from authentik.outposts.tasks import outpost_connection_discovery
from authentik.providers.proxy.models import ProxyProvider
from tests.e2e.utils import SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderProxy(SeleniumTestCase):
    """Proxy and Outpost e2e tests"""

    proxy_container: Container

    def tearDown(self) -> None:
        super().tearDown()
        self.output_container_logs(self.proxy_container)
        self.proxy_container.kill()

    def get_container_specs(self) -> Optional[dict[str, Any]]:
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
            image=self.get_container_image("ghcr.io/goauthentik/dev-proxy"),
            detach=True,
            network_mode="host",
            environment={
                "AUTHENTIK_HOST": self.live_server_url,
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
        )
        return container

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-oauth2.yaml",
        "system/providers-proxy.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_proxy_simple(self):
        """Test simple outpost setup with single provider"""
        # set additionalHeaders to test later
        self.user.attributes["additionalHeaders"] = {"X-Foo": "bar"}
        self.user.save()

        proxy: ProxyProvider = ProxyProvider.objects.create(
            name="proxy_provider",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            internal_host="http://localhost",
            external_host="http://localhost:9000",
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
        outpost.build_user_permissions(outpost.user)

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
        sleep(5)

        self.driver.get("http://localhost:9000")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        self.assertIn(f"X-Authentik-Username: {self.user.username}", full_body_text)
        self.assertIn("X-Foo: bar", full_body_text)

        self.driver.get("http://localhost:9000/outpost.goauthentik.io/sign_out")
        sleep(2)
        full_body_text = self.driver.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of proxy.", full_body_text)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-oauth2.yaml",
        "system/providers-proxy.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_proxy_basic_auth(self):
        """Test simple outpost setup with single provider"""
        cred = generate_id()
        attr = "basic-password"  # nosec
        self.user.attributes["basic-username"] = cred
        self.user.attributes[attr] = cred
        self.user.save()

        proxy: ProxyProvider = ProxyProvider.objects.create(
            name="proxy_provider",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            internal_host="http://localhost",
            external_host="http://localhost:9000",
            basic_auth_enabled=True,
            basic_auth_user_attribute="basic-username",
            basic_auth_password_attribute=attr,
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
        outpost.build_user_permissions(outpost.user)

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
        sleep(5)

        self.driver.get("http://localhost:9000")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        self.assertIn(f"X-Authentik-Username: {self.user.username}", full_body_text)
        auth_header = b64encode(f"{cred}:{cred}".encode()).decode()
        self.assertIn(f"Authorization: Basic {auth_header}", full_body_text)

        self.driver.get("http://localhost:9000/outpost.goauthentik.io/sign_out")
        sleep(2)
        full_body_text = self.driver.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of proxy.", full_body_text)


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderProxyConnect(ChannelsLiveServerTestCase):
    """Test Proxy connectivity over websockets"""

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_proxy_connectivity(self):
        """Test proxy connectivity over websocket"""
        outpost_connection_discovery()  # pylint: disable=no-value-for-parameter
        proxy: ProxyProvider = ProxyProvider.objects.create(
            name=generate_id(),
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            internal_host="http://localhost",
            external_host="http://localhost:9000",
        )
        # Ensure OAuth2 Params are set
        proxy.set_oauth_defaults()
        proxy.save()
        # we need to create an application to actually access the proxy
        Application.objects.create(name="proxy", slug="proxy", provider=proxy)
        service_connection = DockerServiceConnection.objects.get(local=True)
        outpost: Outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.PROXY,
            service_connection=service_connection,
            _config=asdict(OutpostConfig(authentik_host=self.live_server_url, log_level="debug")),
        )
        outpost.providers.add(proxy)
        outpost.build_user_permissions(outpost.user)

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
        self.assertGreaterEqual(len(state), 1)

        # Make sure to delete the outpost to remove the container
        outpost.delete()
