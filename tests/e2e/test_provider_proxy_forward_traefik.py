"""Proxy and Outpost e2e tests"""

from pathlib import Path
from time import sleep
from typing import Any

from docker.models.containers import Container
from selenium.webdriver.common.by import By

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyMode, ProxyProvider
from tests.e2e.utils import SeleniumTestCase, retry


class TestProviderProxyForwardTraefik(SeleniumTestCase):
    """Proxy and Outpost e2e tests"""

    proxy_container: Container

    def get_container_specs(self) -> dict[str, Any] | None:
        return {
            "image": "traefik/whoami:latest",
            "name": "ak-whoami",
        }

    def start_outpost(self, outpost: Outpost):
        """Start proxy container based on outpost created"""
        self.run_container(
            image=self.get_container_image("ghcr.io/goauthentik/dev-proxy"),
            ports={
                "9000": "9000",
            },
            environment={
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
            name="ak-test-outpost",
        )

    def start_reverse_proxy(self):
        local_config_path = (
            Path(__file__).parent / "proxy_forward_auth" / "traefik_single" / "config-static.yaml"
        )
        self.run_container(
            image="docker.io/library/traefik:3.1",
            ports={
                "80": "80",
            },
            volumes={
                local_config_path: {
                    "bind": "/etc/traefik/traefik.yml",
                }
            },
        )

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
        proxy: ProxyProvider = ProxyProvider.objects.create(
            name=generate_id(),
            mode=ProxyMode.FORWARD_SINGLE,
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            internal_host=f"http://{self.host}",
            external_host="http://localhost",
        )
        # Ensure OAuth2 Params are set
        proxy.set_oauth_defaults()
        proxy.save()
        # we need to create an application to actually access the proxy
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=proxy)
        outpost: Outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.PROXY,
        )
        outpost.providers.add(proxy)
        outpost.build_user_permissions(outpost.user)

        self.proxy_container = self.start_outpost(outpost)
        self.rp_container = self.start_reverse_proxy()

        # Wait until outpost healthcheck succeeds
        healthcheck_retries = 0
        while healthcheck_retries < 50:  # noqa: PLR2004
            if len(outpost.state) > 0:
                state = outpost.state[0]
                if state.last_seen:
                    break
            healthcheck_retries += 1
            sleep(0.5)
        sleep(5)

        self.driver.get("http://localhost")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        self.assertIn(f"X-Authentik-Username: {self.user.username}", full_body_text)

        self.driver.get("http://localhost/outpost.goauthentik.io/sign_out")
        sleep(2)
        full_body_text = self.driver.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of", full_body_text)
