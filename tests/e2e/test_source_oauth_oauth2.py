"""test OAuth Source"""

from time import sleep

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from tests.decorators import retry
from tests.e2e.oauth_source import DexOAuthSourceMixin
from tests.selenium import SeleniumTestCase

MAX_REFRESH_RETRIES = 5
INTERFACE_TIMEOUT = 10


class TestSourceOAuth2(DexOAuthSourceMixin, SeleniumTestCase):
    """test OAuth Source flow"""

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
        self.create_source()
        self.driver.get(self.live_server_url)

        self.click_source_button()

        self.login_via_oauth_provider()

        # At this point we've been redirected back
        # and we're asked for the username
        self.enroll_username("foo")

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
        self.click_source_button()

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
        self.create_source()
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
