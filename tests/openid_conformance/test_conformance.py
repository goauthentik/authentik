from json import dumps
from time import sleep
from authentik.blueprints.tests import apply_blueprint, reconcile_app
from tests.e2e.utils import SeleniumTestCase, retry
from tests.openid_conformance.conformance import Conformance
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as ec


class TestOpenIDConformance(SeleniumTestCase):

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
        conformance = Conformance(f"https://{self.host}:8443/", None, verify_ssl=False)

        # Create a test plan instance and print the id of it
        test_plan = conformance.create_test_plan(
            test_plan_name, dumps(test_plan_config), test_variant_config
        )
        plan_id = test_plan["id"]
        n = 0
        for test in test_plan["modules"]:
            with self.subTest(test["testModule"]):
                # Fetch name and variant of the next test to run
                module_name = test["testModule"]
                variant = test["variant"]
                print(f"Module name: {module_name}")
                print(f"Variant: {dumps(variant)}")

                # Create an instance of that test
                module_instance = conformance.create_test_from_plan_with_variant(
                    plan_id, module_name, variant
                )
                module_id = module_instance["id"]
                while True:
                    test_status = conformance.get_test_status(module_id)
                    print(test_status)
                    browser_urls = test_status.get("browser", {}).get("urls", [])
                    print(browser_urls)
                    if len(browser_urls) < 1:
                        continue
                    self.do_browser(browser_urls[0])
                    # Check if we need to upload any items
                    test_log = conformance.get_test_log(module_id)
                    upload_items = [x for x in test_log if "upload" in x]
                    if len(upload_items) > 0:
                        sleep(10)
                        for item in upload_items:
                            conformance.upload_image(
                                module_id, item, self.driver.get_screenshot_as_base64()
                            )
                    # Close tab we've opened earlier
                    # self.driver.close()
                    break
            sleep(2)
            n += 1

    def do_browser(self, url):
        """For any specific OpenID Conformance test, execute the operations required"""
        # self.driver.switch_to.new_window("tab")
        self.driver.get(url)
        if "if/flow/default-authentication-flow" in self.driver.current_url:
            self.login()
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "#complete")))
