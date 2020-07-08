"""test SAML Source"""
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types import Healthcheck
from e2e.utils import SeleniumTestCase
from passbook.crypto.models import CertificateKeyPair
from passbook.flows.models import Flow
from passbook.sources.saml.models import SAMLBindingTypes, SAMLSource

IDP_CERT = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJALmVVuDWu4NYMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTYxMjMxMTQzNDQ3WhcNNDgwNjI1MTQzNDQ3WjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAzUCFozgNb1h1M0jzNRSCjhOBnR+uVbVpaWfXYIR+AhWDdEe5ryY+Cgav
Og8bfLybyzFdehlYdDRgkedEB/GjG8aJw06l0qF4jDOAw0kEygWCu2mcH7XOxRt+
YAH3TVHa/Hu1W3WjzkobqqqLQ8gkKWWM27fOgAZ6GieaJBN6VBSMMcPey3HWLBmc
+TYJmv1dbaO2jHhKh8pfKw0W12VM8P1PIO8gv4Phu/uuJYieBWKixBEyy0lHjyix
YFCR12xdh4CA47q958ZRGnnDUGFVE1QhgRacJCOZ9bd5t9mr8KLaVBYTCJo5ERE8
jymab5dPqe5qKfJsCZiqWglbjUo9twIDAQABo1AwTjAdBgNVHQ4EFgQUxpuwcs/C
YQOyui+r1G+3KxBNhxkwHwYDVR0jBBgwFoAUxpuwcs/CYQOyui+r1G+3KxBNhxkw
DAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAAiWUKs/2x/viNCKi3Y6b
lEuCtAGhzOOZ9EjrvJ8+COH3Rag3tVBWrcBZ3/uhhPq5gy9lqw4OkvEws99/5jFs
X1FJ6MKBgqfuy7yh5s1YfM0ANHYczMmYpZeAcQf2CGAaVfwTTfSlzNLsF2lW/ly7
yapFzlYSJLGoVE+OHEu8g5SlNACUEfkXw+5Eghh+KzlIN7R6Q7r2ixWNFBC/jWf7
NKUfJyX8qIG5md1YUeT6GBW9Bm2/1/RiO24JTaYlfLdKK9TYb8sG5B+OLab2DImG
99CJ25RkAcSobWNF5zD0O6lgOo3cEdB/ksCq3hmtlC/DlLZ/D8CJ+7VuZnS1rR2n
aQ==
-----END CERTIFICATE-----"""


class TestSourceSAML(SeleniumTestCase):
    """test SAML Source flow"""

    def setUp(self):
        super().setUp()
        self.container = self.setup_client()

    def setup_client(self) -> Container:
        """Setup test IdP container"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="kristophjunge/test-saml-idp",
            detach=True,
            network_mode="host",
            auto_remove=True,
            healthcheck=Healthcheck(
                test=["CMD", "curl", "http://localhost:8080"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
            environment={
                "SIMPLESAMLPHP_SP_ENTITY_ID": "entity-id",
                "SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE": (
                    f"{self.live_server_url}/source/saml/saml-idp-test/acs/"
                ),
            },
        )
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            sleep(1)

    def tearDown(self):
        self.container.kill()
        super().tearDown()

    def test_idp_redirect(self):
        """test SAML Source With redirect binding"""
        sleep(1)
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        keypair = CertificateKeyPair.objects.create(
            name="test-idp-cert", certificate_data=IDP_CERT
        )

        SAMLSource.objects.create(
            name="saml-idp-test",
            slug="saml-idp-test",
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            issuer="entity-id",
            sso_url="http://localhost:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.Redirect,
            signing_kp=keypair,
        )

        self.driver.get(self.live_server_url)

        self.wait.until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, "pf-c-login__main-footer-links-item-link")
            )
        )
        self.driver.find_element(
            By.CLASS_NAME, "pf-c-login__main-footer-links-item-link"
        ).click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(
            ec.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/-/user/')]")
            )
        )
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").click()

        # Wait until we've loaded the user info page
        self.wait.until(ec.presence_of_element_located((By.ID, "id_username")))
        self.assertNotEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), ""
        )

    def test_idp_post(self):
        """test SAML Source With post binding"""
        sleep(1)
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        keypair = CertificateKeyPair.objects.create(
            name="test-idp-cert", certificate_data=IDP_CERT
        )

        SAMLSource.objects.create(
            name="saml-idp-test",
            slug="saml-idp-test",
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            issuer="entity-id",
            sso_url="http://localhost:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.POST,
            signing_kp=keypair,
        )

        self.driver.get(self.live_server_url)

        self.wait.until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, "pf-c-login__main-footer-links-item-link")
            )
        )
        self.driver.find_element(
            By.CLASS_NAME, "pf-c-login__main-footer-links-item-link"
        ).click()
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(
            ec.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/-/user/')]")
            )
        )
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").click()

        # Wait until we've loaded the user info page
        self.wait.until(ec.presence_of_element_located((By.ID, "id_username")))
        self.assertNotEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), ""
        )

    def test_idp_post_auto(self):
        """test SAML Source With post binding (auto redirect)"""
        sleep(1)
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        keypair = CertificateKeyPair.objects.create(
            name="test-idp-cert", certificate_data=IDP_CERT
        )

        SAMLSource.objects.create(
            name="saml-idp-test",
            slug="saml-idp-test",
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            issuer="entity-id",
            sso_url="http://localhost:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.POST_AUTO,
            signing_kp=keypair,
        )

        self.driver.get(self.live_server_url)

        self.wait.until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, "pf-c-login__main-footer-links-item-link")
            )
        )
        self.driver.find_element(
            By.CLASS_NAME, "pf-c-login__main-footer-links-item-link"
        ).click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(
            ec.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/-/user/')]")
            )
        )
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").click()

        # Wait until we've loaded the user info page
        self.wait.until(ec.presence_of_element_located((By.ID, "id_username")))
        self.assertNotEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), ""
        )
