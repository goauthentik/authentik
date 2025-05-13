"""Proxy and Outpost e2e tests"""

from base64 import b64encode
from dataclasses import asdict
from json import loads
from sys import platform
from time import sleep
from unittest.case import skip, skipUnless
from unittest.mock import patch

from channels.testing import ChannelsLiveServerTestCase
from jwt import decode
from selenium.webdriver.common.by import By

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import DockerServiceConnection, Outpost, OutpostConfig, OutpostType
from authentik.outposts.tasks import outpost_connection_discovery
from authentik.outposts.tests.test_ws import patched__get_ct_cached
from authentik.providers.proxy.models import ProxyProvider
from tests.e2e.utils import SeleniumTestCase, retry


@patch("guardian.shortcuts._get_ct_cached", patched__get_ct_cached)
class TestProviderProxy(SeleniumTestCase):
    """Proxy and Outpost e2e tests"""

    def setUp(self):
        super().setUp()
        self.run_container(
            image="traefik/whoami:latest",
            ports={
                "80": "80",
            },
        )

    def start_proxy(self, outpost: Outpost):
        """Start proxy container based on outpost created"""
        self.run_container(
            image=self.get_container_image("ghcr.io/goauthentik/dev-proxy"),
            ports={
                "9000": "9000",
            },
            environment={
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
        )

    @retry()
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
    def test_proxy_simple(self):
        """Test simple outpost setup with single provider"""
        # set additionalHeaders to test later
        self.user.attributes["additionalHeaders"] = {"X-Foo": "bar"}
        self.user.save()

        proxy: ProxyProvider = ProxyProvider.objects.create(
            name=generate_id(),
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            invalidation_flow=Flow.objects.get(slug="default-provider-invalidation-flow"),
            internal_host=f"http://{self.host}",
            external_host="http://localhost:9000",
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

        self.start_proxy(outpost)

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

        self.driver.get("http://localhost:9000/api")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        body = loads(full_body_text)

        self.assertEqual(body["headers"]["X-Authentik-Username"], [self.user.username])
        self.assertEqual(body["headers"]["X-Foo"], ["bar"])
        raw_jwt: str = body["headers"]["X-Authentik-Jwt"][0]
        jwt = decode(raw_jwt, options={"verify_signature": False})

        self.assertIsNotNone(jwt["sid"])
        self.assertIsNotNone(jwt["ak_proxy"])

        self.driver.get("http://localhost:9000/outpost.goauthentik.io/sign_out")
        sleep(2)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        session_end_stage = self.get_shadow_root("ak-stage-session-end", flow_executor)
        title = session_end_stage.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of", title)

    @retry()
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
    def test_proxy_basic_auth(self):
        """Test simple outpost setup with single provider"""
        cred = generate_id()
        attr = "basic-password"  # nosec
        self.user.attributes["basic-username"] = cred
        self.user.attributes[attr] = cred
        self.user.save()

        proxy: ProxyProvider = ProxyProvider.objects.create(
            name=generate_id(),
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            invalidation_flow=Flow.objects.get(slug="default-provider-invalidation-flow"),
            internal_host=f"http://{self.host}",
            external_host="http://localhost:9000",
            basic_auth_enabled=True,
            basic_auth_user_attribute="basic-username",
            basic_auth_password_attribute=attr,
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

        self.start_proxy(outpost)

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

        self.driver.get("http://localhost:9000/api")
        self.login()
        sleep(1)

        full_body_text = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        body = loads(full_body_text)

        self.assertEqual(body["headers"]["X-Authentik-Username"], [self.user.username])
        auth_header = b64encode(f"{cred}:{cred}".encode()).decode()
        self.assertEqual(body["headers"]["Authorization"], [f"Basic {auth_header}"])

        self.driver.get("http://localhost:9000/outpost.goauthentik.io/sign_out")
        sleep(2)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        session_end_stage = self.get_shadow_root("ak-stage-session-end", flow_executor)
        title = session_end_stage.find_element(By.CSS_SELECTOR, ".pf-c-title.pf-m-3xl").text
        self.assertIn("You've logged out of", title)


# TODO: Fix flaky test
@skip("Flaky test")
@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderProxyConnect(ChannelsLiveServerTestCase):
    """Test Proxy connectivity over websockets"""

    @retry(exceptions=[AssertionError])
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
        outpost_connection_discovery()
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
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=proxy)
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
        while healthcheck_retries < 50:  # noqa: PLR2004
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
