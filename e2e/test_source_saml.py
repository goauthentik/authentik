"""test SAML Source"""
from sys import platform
from time import sleep
from unittest.case import skipUnless

from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from structlog import get_logger

from e2e.utils import SeleniumTestCase
from passbook.crypto.models import CertificateKeyPair
from passbook.flows.models import Flow
from passbook.sources.saml.models import SAMLBindingTypes, SAMLSource

LOGGER = get_logger()

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

IDP_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDNQIWjOA1vWHUz
SPM1FIKOE4GdH65VtWlpZ9dghH4CFYN0R7mvJj4KBq86Dxt8vJvLMV16GVh0NGCR
50QH8aMbxonDTqXSoXiMM4DDSQTKBYK7aZwftc7FG35gAfdNUdr8e7VbdaPOShuq
qotDyCQpZYzbt86ABnoaJ5okE3pUFIwxw97LcdYsGZz5Ngma/V1to7aMeEqHyl8r
DRbXZUzw/U8g7yC/g+G7+64liJ4FYqLEETLLSUePKLFgUJHXbF2HgIDjur3nxlEa
ecNQYVUTVCGBFpwkI5n1t3m32avwotpUFhMImjkRETyPKZpvl0+p7mop8mwJmKpa
CVuNSj23AgMBAAECggEABn4I/B20xxXcNzASiVZJvua9DdRHtmxTlkLznBj0x2oY
y1/Nbs3d3oFRn5uEuhBZOTcphsgwdRSHDXZsP3gUObew+d2N/zieUIj8hLDVlvJP
rU/s4U/l53Q0LiNByE9ThvL+zJLPCKJtd5uHZjB5fFm69+Q7gu8xg4xHIub+0pP5
PHanmHCDrbgNN/oqlar4FZ2MXTgekW6Amyc/koE9hIn4Baa2Ke/B/AUGY4pMRLqp
TArt+GTVeWeoFY9QACUpaHpJhGb/Piou6tlU57e42cLoki1f0+SARsBBKyXA7BB1
1fMH10KQYFA68dTYWlKzQau/K4xaqg4FKmtwF66GQQKBgQD9OpNUS7oRxMHVJaBR
TNWW+V1FXycqojekFpDijPb2X5CWV16oeWgaXp0nOHFdy9EWs3GtGpfZasaRVHsX
SHtPh4Nb8JqHdGE0/CD6t0+4Dns8Bn9cSqtdQB7R3Jn7IMXi9X/U8LDKo+A18/Jq
V8VgUngMny9YjMkQIbK8TRWkYQKBgQDPf4nxO6ju+tOHHORQty3bYDD0+OV3I0+L
0yz0uPreryBVi9nY43KakH52D7UZEwwsBjjGXD+WH8xEsmBWsGNXJu025PvzIJoz
lAEiXvMp/NmYp+tY4rDmO8RhyVocBqWHzh38m0IFOd4ByFD5nLEDrA3pDVo0aNgY
n0GwRysZFwKBgQDkCj3m6ZMUsUWEty+aR0EJhmKyODBDOnY09IVhH2S/FexVFzUN
LtfK9206hp/Awez3Ln2uT4Zzqq5K7fMzUniJdBWdVB004l8voeXpIe9OZuwfcBJ9
gFi1zypx/uFDv421BzQpBN+QfOdKbvbdQVFjnqCxbSDr80yVlGMrI5fbwQKBgG09
oRrepO7EIO8GN/GCruLK/ptKGkyhy3Q6xnVEmdb47hX7ncJA5IoZPmrblCVSUNsw
n11XHabksL8OBgg9rt8oQEThQv/aDzTOW9aDlJNragejiBTwq99aYeZ1gjo1CZq4
2jKubpCfyZC4rGDtrIfZYi1q+S2UcQhtd8DdhwQbAoGAAM4EpDA4yHB5yiek1p/o
CbqRCta/Dx6Eyo0KlNAyPuFPAshupG4NBx7mT2ASfL+2VBHoi6mHSri+BDX5ryYF
fMYvp7URYoq7w7qivRlvvEg5yoYrK13F2+Gj6xJ4jEN9m0KdM/g3mJGq0HBTIQrp
Sm75WXsflOxuTn08LbgGc4s=
-----END PRIVATE KEY-----"""


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestSourceSAML(SeleniumTestCase):
    """test SAML Source flow"""

    def setUp(self):
        self.container = self.setup_client()
        super().setUp()

    def setup_client(self) -> Container:
        """Setup test IdP container"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="kristophjunge/test-saml-idp:1.15",
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
            LOGGER.info("Container failed healthcheck")
            sleep(1)

    def test_idp_redirect(self):
        """test SAML Source With redirect binding"""
        sleep(1)
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        keypair = CertificateKeyPair.objects.create(
            name="test-idp-cert", certificate_data=IDP_CERT, key_data=IDP_KEY,
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
            name="test-idp-cert", certificate_data=IDP_CERT, key_data=IDP_KEY,
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
        sleep(1)
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
            name="test-idp-cert", certificate_data=IDP_CERT, key_data=IDP_KEY,
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
