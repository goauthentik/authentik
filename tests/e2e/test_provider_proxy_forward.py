"""Proxy and Outpost e2e tests"""

from json import loads
from pathlib import Path
from time import sleep
from unittest import skip

from selenium.webdriver.common.by import By

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyMode, ProxyProvider
from tests.e2e.utils import SeleniumTestCase, retry


class TestProviderProxyForward(SeleniumTestCase):
    """Proxy and Outpost e2e tests"""

    def setUp(self):
        super().setUp()
        self.run_container(
            image="traefik/whoami:latest",
            name="ak-whoami",
        )

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

    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
        "default/flow-default-provider-invalidation.yaml",
    )
    @apply_blueprint(
        "system/providers-oauth2.yaml",
        "system/providers-proxy.yaml",
    )
    @reconcile_app("authentik_crypto")
    def prepare(self):
        proxy: ProxyProvider = ProxyProvider.objects.create(
            name=generate_id(),
            mode=ProxyMode.FORWARD_SINGLE,
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            invalidation_flow=Flow.objects.get(slug="default-provider-invalidation-flow"),
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

        self.start_outpost(outpost)
        self.wait_for_outpost(outpost)

    @retry()
    def test_traefik(self):
        """Test traefik"""
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

        self.prepare()

        self.driver.get("http://localhost/api")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        body = loads(full_body_text)

        self.assertEqual(body["headers"]["X-Authentik-Username"], [self.user.username])

        self.driver.get("http://localhost/outpost.goauthentik.io/sign_out")
        sleep(2)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        session_end_stage = self.get_shadow_root("ak-stage-session-end", flow_executor)
        title = session_end_stage.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of", title)

    @skip("Flaky test")
    @retry()
    def test_nginx(self):
        """Test nginx"""
        self.prepare()

        # Start nginx last so all hosts are resolvable, otherwise nginx exits
        self.run_container(
            image="docker.io/library/nginx:1.27",
            ports={
                "80": "80",
            },
            volumes={
                f"{Path(__file__).parent / "proxy_forward_auth" / "nginx_single" / "nginx.conf"}": {
                    "bind": "/etc/nginx/conf.d/default.conf",
                }
            },
        )

        self.driver.get("http://localhost/api")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        body = loads(full_body_text)

        self.assertEqual(body["headers"]["X-Authentik-Username"], [self.user.username])

        self.driver.get("http://localhost/outpost.goauthentik.io/sign_out")
        sleep(2)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        session_end_stage = self.get_shadow_root("ak-stage-session-end", flow_executor)
        title = session_end_stage.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of", title)

    @retry()
    def test_envoy(self):
        """Test envoy"""
        self.run_container(
            image="docker.io/envoyproxy/envoy:v1.25-latest",
            ports={
                "10000": "80",
            },
            volumes={
                f"{Path(__file__).parent / "proxy_forward_auth" / "envoy_single" / "envoy.yaml"}": {
                    "bind": "/etc/envoy/envoy.yaml",
                }
            },
        )

        self.prepare()

        self.driver.get("http://localhost/api")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        body = loads(full_body_text)

        self.assertEqual(body["headers"]["X-Authentik-Username"], [self.user.username])

        self.driver.get("http://localhost/outpost.goauthentik.io/sign_out")
        sleep(2)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        session_end_stage = self.get_shadow_root("ak-stage-session-end", flow_executor)
        title = session_end_stage.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of", title)

    @retry()
    def test_caddy(self):
        """Test caddy"""
        local_config_path = (
            Path(__file__).parent / "proxy_forward_auth" / "caddy_single" / "Caddyfile"
        )
        self.run_container(
            image="docker.io/library/caddy:2.8",
            ports={
                "80": "80",
            },
            volumes={
                local_config_path: {
                    "bind": "/etc/caddy/Caddyfile",
                }
            },
        )

        self.prepare()

        self.driver.get("http://localhost/api")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        body = loads(full_body_text)

        self.assertEqual(body["headers"]["X-Authentik-Username"], [self.user.username])

        self.driver.get("http://localhost/outpost.goauthentik.io/sign_out")
        sleep(2)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        session_end_stage = self.get_shadow_root("ak-stage-session-end", flow_executor)
        title = session_end_stage.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of", title)
