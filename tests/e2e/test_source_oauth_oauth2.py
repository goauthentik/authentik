"""test OAuth Source"""

from pathlib import Path
from time import sleep

from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import NoSuchElementException, SeleniumTestCase, TimeoutException, retry

MAX_REFRESH_RETRIES = 5
INTERFACE_TIMEOUT = 10


class TestSourceOAuth2(SeleniumTestCase):
    """test OAuth Source flow"""

    def setUp(self):
        self.client_secret = generate_id()
        self.slug = generate_id()
        super().setUp()
        self.run_container(
            image="ghcr.io/dexidp/dex:v2.44.0",
            ports={"5556": "5556"},
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:5556/dex/healthz"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
            environment={
                "AK_HOST": self.host,
                "AK_REDIRECT_URL": self.url(
                    "authentik_sources_oauth:oauth-client-callback",
                    source_slug=self.slug,
                ),
                "AK_CLIENT_SECRET": self.client_secret,
            },
            volumes={
                f"{Path(__file__).parent / "sources_oauth2_dex" / "dex.yaml"}": {
                    "bind": "/etc/dex/config.docker.yaml",
                }
            },
        )

    def find_settings_tab_panel(self, tab_name: str, panel_content_selector: str):
        """Find a settings tab panel by name"""
        url_after_login = self.driver.current_url

        user_settings_url = self.if_user_url("/settings")
        hash_route = ';%7B"page"%3A"page-' + tab_name + '"%7D'

        self.driver.get(user_settings_url + hash_route)

        # A refresh is required because the hash change doesn't always trigger a reload.
        self.driver.refresh()

        try:
            self.wait.until(ec.url_contains(user_settings_url))
        except TimeoutException:
            self.fail(
                f"Timed out waiting for user settings page"
                f"Initial URL after OAuth linking: {url_after_login} "
                f"Current URL: {self.driver.current_url} "
                f"Expected URL: {user_settings_url})"
            )

        try:
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "ak-interface-user")))
        except TimeoutException:
            context = self.driver.find_element(By.TAG_NAME, "body")
            inner_html = context.get_attribute("innerHTML") or ""

            snippet = context.text.strip()[:1000].replace("\n", " ")

            self.fail(
                f"Timed out waiting for element text to appear at {self.driver.current_url}. "
                f"Current content: {snippet or '<empty>'}"
                f"{inner_html or '<empty>'}"
            )

        interface = self.driver.find_element(By.CSS_SELECTOR, "ak-interface-user").shadow_root

        user_settings = interface.find_element(By.CSS_SELECTOR, "ak-user-settings").shadow_root

        tab_panel = user_settings.find_element(By.CSS_SELECTOR, panel_content_selector).shadow_root

        return tab_panel

    def create_objects(self):
        """Create required objects"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")

        source = OAuthSource.objects.create(  # nosec
            name=generate_id(),
            slug=self.slug,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            provider_type="openidconnect",
            authorization_url=f"http://{self.host}:5556/dex/auth",
            access_token_url=f"http://{self.host}:5556/dex/token",
            profile_url=f"http://{self.host}:5556/dex/userinfo",
            consumer_key="example-app",
            consumer_secret=self.client_secret,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()

    def login_via_oauth_provider(self):
        """Perform login at the OAuth provider (Dex)"""
        self.wait.until(ec.presence_of_element_located((By.ID, "login")))

        initial_provider_url = self.driver.current_url

        self.driver.find_element(By.ID, "login").send_keys("admin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]")))

        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        self.wait.until(ec.url_changes(initial_provider_url))

        self.assertNotEqual(
            initial_provider_url,
            self.driver.current_url,
            "Expected to be redirected after login at OAuth provider",
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-source-authentication.yaml",
        "default/flow-default-source-enrollment.yaml",
        "default/flow-default-source-pre-authentication.yaml",
    )
    def test_oauth_enroll(self):
        """test OAuth Source With With OIDC"""
        self.create_objects()
        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, "fieldset[name='login-sources'] button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, "fieldset[name='login-sources'] button"
        ).click()

        self.login_via_oauth_provider()

        # At this point we've been redirected back
        # and we're asked for the username
        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)

        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").click()
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys("foo")
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys(Keys.ENTER)

        # Wait until we've logged in
        self.wait_for_url(self.if_user_url())

        self.assert_user(User(username="foo", name="admin", email="admin@example.com"))

    @retry()
    def test_oauth_enroll_auth(self):
        """test OAuth Source With With OIDC (enroll and authenticate again)"""
        self.test_oauth_enroll()
        # We're logged in at the end of this, log out and re-login
        self.driver.get(self.url("authentik_flows:default-invalidation"))
        sleep(1)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, "fieldset[name='login-sources'] button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, "fieldset[name='login-sources'] button"
        ).click()

        self.login_via_oauth_provider()

        self.wait.until(ec.url_matches(self.if_user_url()))

        self.assert_user(User(username="foo", name="admin", email="admin@example.com"))

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-source-authentication.yaml",
        "default/flow-default-source-enrollment.yaml",
        "default/flow-default-source-pre-authentication.yaml",
    )
    def test_oauth_link(self) -> None:
        """
        Test OAuth Source link OIDC

        This test will enroll the user via OAuth, then log in as admin and link the OAuth
        source to the admin user.
        """
        self.create_objects()
        self.driver.get(self.live_server_url)
        self.login()

        # Ensure that a stable session is created before linking.
        sleep(3)

        self.driver.get(
            self.url("authentik_sources_oauth:oauth-client-login", source_slug=self.slug)
        )

        self.login_via_oauth_provider()

        post_login_expected_url = self.if_user_url("/settings;page-sources")

        self.assertEqual(
            self.driver.current_url,
            post_login_expected_url,
            "Expected to be redirected to user settings after linking OAuth source",
        )

        selector = f"[data-test-id=source-settings-list-item][data-slug='{self.slug}']"
        sourceElement = None

        for attempt in range(MAX_REFRESH_RETRIES):
            source_settings_tab_panel = self.find_settings_tab_panel(
                "sources", "ak-user-settings-source"
            )

            try:
                sourceElement = source_settings_tab_panel.find_element(By.CSS_SELECTOR, selector)
            except NoSuchElementException:
                sourceElement = None

            if sourceElement:
                break

            if attempt < MAX_REFRESH_RETRIES - 1:
                self.logger.debug(
                    f"[Attempt {attempt + 1}/{MAX_REFRESH_RETRIES}] No results yet, sleeping 1s… "
                    f"(Current URL: {self.driver.current_url})"
                )

                sleep(1)

        if not sourceElement:
            context = self.driver.find_element(By.TAG_NAME, "body")
            inner_html = context.get_attribute("innerHTML") or ""

            snippet = context.text.strip()[:1000].replace("\n", " ")

            self.fail(
                f"Selector '{selector}' not found at {self.driver.current_url}"
                f" after {MAX_REFRESH_RETRIES} retries. "
                f"Current content: {snippet or '<empty>'}"
                f"{inner_html or '<empty>'}"
            )

        data_source_component_attribute = sourceElement.get_attribute("data-source-component")

        self.assertIsNotNone(
            data_source_component_attribute,
            f"Source Component not found in source element at {self.driver.current_url}",
        )

        self.assertEqual(
            data_source_component_attribute,
            "ak-user-settings-source-oauth",
            "Unexpected source component",
        )

        connection_user_pk_attribute = sourceElement.get_attribute("data-connection-user-pk")

        self.assertIsNotNone(
            connection_user_pk_attribute,
            f"Connection User PK not found in source element at {self.driver.current_url}",
        )

        self.assertEqual(
            int(connection_user_pk_attribute),
            self.user.pk,
            f"Unexpected user {self.driver.current_url}",
        )
