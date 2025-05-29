from json import dumps
from time import sleep
from authentik.blueprints.tests import apply_blueprint, reconcile_app
from tests.e2e.utils import SeleniumTestCase, retry
from tests.openid_conformance.conformance import Conformance
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as ec


class TestOpenIDConformance(SeleniumTestCase):

    conformance: Conformance

    @retry()
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
    def test_oidcc_basic_certification_test(self):
        test_plan_name = "oidcc-basic-certification-test-plan"
        test_variant_config = {
            "server_metadata": "discovery",
            "client_registration": "static_client",
        }
        test_plan_config = {
            "alias": "authentik",
            "description": "authentik",
            "server": {
                "discoveryUrl": f"{self.live_server_url}/application/o/conformance/.well-known/openid-configuration"
            },
            "client": {
                "client_id": "4054d882aff59755f2f279968b97ce8806a926e1",
                "client_secret": "4c7e4933009437fb486b5389d15b173109a0555dc47e0cc0949104f1925bcc6565351cb1dffd7e6818cf074f5bd50c210b565121a7328ee8bd40107fc4bbd867",
            },
            "client_secret_post": {
                "client_id": "4054d882aff59755f2f279968b97ce8806a926e1",
                "client_secret": "4c7e4933009437fb486b5389d15b173109a0555dc47e0cc0949104f1925bcc6565351cb1dffd7e6818cf074f5bd50c210b565121a7328ee8bd40107fc4bbd867",
            },
            "client2": {
                "client_id": "ad64aeaf1efe388ecf4d28fcc537e8de08bcae26",
                "client_secret": "ff2e34a5b04c99acaf7241e25a950e7f6134c86936923d8c698d8f38bd57647750d661069612c0ee55045e29fe06aa101804bdae38e8360647d595e771fea789",
            },
            "consent": {},
        }

        # Create a Conformance instance...
        self.conformance = Conformance(f"https://{self.host}:8443/", None, verify_ssl=False)

        test_plan = self.conformance.create_test_plan(
            test_plan_name, dumps(test_plan_config), test_variant_config
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
                self.run_test(module_id)
                self.conformance.wait_for_state(module_id, ["FINISHED"], timeout=self.wait_timeout)
            sleep(2)

    def run_test(self, module_id: str):
        tested_browser_url = 0
        uploaded_image = 0
        while True:
            # Fetch all info
            test_status = self.conformance.get_test_status(module_id)
            test_log = self.conformance.get_test_log(module_id)
            test_info = self.conformance.get_module_info(module_id)
            # Check if we need to clear cookies - tests only indicates this in their written summary
            # so this check is a bit brittle
            if "cookies" in test_info["summary"]:
                self.driver.delete_all_cookies()
            # Check if we need deal with any browser URLs
            browser_urls = test_status.get("browser", {}).get("urls", [])
            if len(browser_urls) > tested_browser_url:
                self.do_browser(browser_urls[tested_browser_url])
                tested_browser_url += 1
            # Check if we need to upload any items
            upload_items = [x for x in test_log if "upload" in x]
            if len(upload_items) > uploaded_image:
                screenshot = self.get_screenshot()
                self.conformance.upload_image(
                    module_id, upload_items[uploaded_image]["upload"], screenshot
                )
                sleep(3)
                uploaded_image += 1
            if test_info["status"] in ["INTERRUPTED", "FINISHED"]:
                return

    def get_screenshot(self):
        """Get a screenshot, but resize the window first so we don't exceed 500kb"""
        self.driver.set_window_size(800, 600)
        screenshot = f"data:image/jpeg;base64,{self.driver.get_screenshot_as_base64()}"
        self.driver.maximize_window()
        return screenshot

    def do_browser(self, url):
        """For any specific OpenID Conformance test, execute the operations required"""
        # self.driver.switch_to.new_window("tab")
        self.driver.get(url)
        if "if/flow/default-authentication-flow" in self.driver.current_url:
            self.login()
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "#complete")))
