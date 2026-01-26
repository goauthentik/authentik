from os import makedirs
from pathlib import Path
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.providers.oauth2.models import OAuth2Provider
from tests.e2e.utils import SeleniumTestCase
from tests.openid_conformance.conformance import Conformance


class TestOpenIDConformance(SeleniumTestCase):

    conformance: Conformance

    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
        "default/flow-default-provider-invalidation.yaml",
    )
    @apply_blueprint("system/providers-oauth2.yaml")
    @reconcile_app("authentik_crypto")
    @apply_blueprint("testing/oidc-conformance.yaml")
    def setUp(self):
        super().setUp()
        makedirs(Path(__file__).parent / "exports", exist_ok=True)
        provider_a = OAuth2Provider.objects.get(
            client_id="4054d882aff59755f2f279968b97ce8806a926e1"
        )
        provider_b = OAuth2Provider.objects.get(
            client_id="ad64aeaf1efe388ecf4d28fcc537e8de08bcae26"
        )
        self.test_plan_config = {
            "alias": "authentik",
            "description": "authentik",
            "server": {
                "discoveryUrl": self.url(
                    "authentik_providers_oauth2:provider-info",
                    application_slug="oidc-conformance-1",
                ),
            },
            "client": {
                "client_id": "4054d882aff59755f2f279968b97ce8806a926e1",
                "client_secret": provider_a.client_secret,
            },
            "client_secret_post": {
                "client_id": "4054d882aff59755f2f279968b97ce8806a926e1",
                "client_secret": provider_a.client_secret,
            },
            "client2": {
                "client_id": "ad64aeaf1efe388ecf4d28fcc537e8de08bcae26",
                "client_secret": provider_b.client_secret,
            },
            "consent": {},
        }
        self.test_variant = {
            "server_metadata": "discovery",
            "client_registration": "static_client",
        }

    def run_test(self, test_name: str, test_plan_config: dict):
        # Create a Conformance instance...
        self.conformance = Conformance(f"https://{self.host}:8443/", None, verify_ssl=False)

        test_plan = self.conformance.create_test_plan(
            test_name,
            test_plan_config,
            self.test_variant,
        )
        plan_id = test_plan["id"]
        for test in test_plan["modules"]:
            with self.subTest(test["testModule"], **test["variant"]):
                # Fetch name and variant of the next test to run
                module_name = test["testModule"]
                variant = test["variant"]
                module_instance = self.conformance.create_test_from_plan_with_variant(
                    plan_id, module_name, variant
                )
                module_id = module_instance["id"]
                self.run_single_test(module_id)
                self.conformance.wait_for_state(module_id, ["FINISHED"], timeout=self.wait_timeout)
            sleep(2)
        self.conformance.export_html(plan_id, Path(__file__).parent / "exports")

    def run_single_test(self, module_id: str):
        """Process instructions for a single test, navigate to browser URLs and take screenshots"""
        tested_browser_url = 0
        uploaded_image = 0
        cleared_cookies = False
        while True:
            # Fetch all info
            test_status = self.conformance.get_test_status(module_id)
            test_log = self.conformance.get_test_log(module_id)
            test_info = self.conformance.get_module_info(module_id)
            # Check status early, if we're finished already we don't want to do anything extra
            if test_info["status"] in ["INTERRUPTED", "FINISHED"]:
                return
            # Check if we need to clear cookies - tests only indicates this in their written summary
            # so this check is a bit brittle
            if "cookies" in test_info["summary"] and not cleared_cookies:
                # Navigate to our origin to delete cookies in the right context
                self.driver.get(self.url("authentik_api:user-me") + "?format=json")
                self.driver.delete_all_cookies()
                cleared_cookies = True
            # Check if we need deal with any browser URLs
            browser_urls = test_status.get("browser", {}).get("urls", [])
            if len(browser_urls) > tested_browser_url:
                self.do_browser(browser_urls[tested_browser_url])
                tested_browser_url += 1
                continue
            # Check if we need to upload any items
            upload_items = [x for x in test_log if "upload" in x]
            if len(upload_items) > uploaded_image:
                screenshot = self.get_screenshot()
                self.conformance.upload_image(
                    module_id, upload_items[uploaded_image]["upload"], screenshot
                )
                sleep(3)
                uploaded_image += 1
                continue
            sleep(0.1)

    def get_screenshot(self):
        """Get a screenshot, but resize the window first so we don't exceed 500kb"""
        self.driver.set_window_size(800, 600)
        screenshot = f"data:image/jpeg;base64,{self.driver.get_screenshot_as_base64()}"
        self.driver.maximize_window()
        return screenshot

    def do_browser(self, url):
        """For any specific OpenID Conformance test, execute the operations required"""
        self.driver.get(url)
        should_expect_completion = False
        if "if/flow/default-authentication-flow" in self.driver.current_url:
            self.logger.debug("Logging in")
            self.login()
            should_expect_completion = True
        if "prompt=consent" in url or "offline_access" in url:
            self.logger.debug("Authorizing")
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "ak-flow-executor")))
            sleep(1)
            flow_executor = self.get_shadow_root("ak-flow-executor")
            consent_stage = self.get_shadow_root("ak-stage-consent", flow_executor)
            consent_stage.find_element(
                By.CSS_SELECTOR,
                "[type=submit]",
            ).click()
            should_expect_completion = True
        if should_expect_completion:
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "#complete")))
