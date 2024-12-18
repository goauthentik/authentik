"""test SAML Source"""

from pathlib import Path
from time import sleep

from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import SeleniumTestCase, retry

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


class TestSourceSAML(SeleniumTestCase):
    """test SAML Source flow"""

    def setUp(self):
        self.slug = generate_id()
        super().setUp()
        self.run_container(
            image="kristophjunge/test-saml-idp:1.15",
            ports={"8080": "8080"},
            healthcheck=Healthcheck(
                test=["CMD", "curl", "http://localhost:8080"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
            volumes={
                str(
                    (Path(__file__).parent / Path("test-saml-idp/saml20-sp-remote.php")).absolute()
                ): {
                    "bind": "/var/www/simplesamlphp/metadata/saml20-sp-remote.php",
                    "mode": "ro",
                }
            },
            environment={
                "SIMPLESAMLPHP_SP_ENTITY_ID": "entity-id",
                "SIMPLESAMLPHP_SP_NAME_ID_FORMAT": (
                    "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                ),
                "SIMPLESAMLPHP_SP_NAME_ID_ATTRIBUTE": "email",
                "SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE": (
                    self.url("authentik_sources_saml:acs", source_slug=self.slug)
                ),
            },
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
    def test_idp_redirect(self):
        """test SAML Source With redirect binding"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        pre_authentication_flow = Flow.objects.get(slug="default-source-pre-authentication")
        keypair = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=IDP_CERT,
            key_data=IDP_KEY,
        )

        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=self.slug,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            pre_authentication_flow=pre_authentication_flow,
            issuer="entity-id",
            sso_url=f"http://{self.host}:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.REDIRECT,
            signing_kp=keypair,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()

        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait_for_url(self.if_user_url())

        self.assert_user(
            User.objects.exclude(username="akadmin")
            .exclude(username__startswith="ak-outpost")
            .exclude_anonymous()
            .exclude(pk=self.user.pk)
            .first()
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
    def test_idp_post(self):
        """test SAML Source With post binding"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        pre_authentication_flow = Flow.objects.get(slug="default-source-pre-authentication")
        keypair = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=IDP_CERT,
            key_data=IDP_KEY,
        )

        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=self.slug,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            pre_authentication_flow=pre_authentication_flow,
            issuer="entity-id",
            sso_url=f"http://{self.host}:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.POST,
            signing_kp=keypair,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()

        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()
        sleep(1)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        consent_stage = self.get_shadow_root("ak-stage-consent", flow_executor)

        self.assertIn(
            source.name,
            consent_stage.find_element(By.CSS_SELECTOR, "#header-text").text,
        )
        consent_stage.find_element(
            By.CSS_SELECTOR,
            "[type=submit]",
        ).click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait_for_url(self.if_user_url())

        self.assert_user(
            User.objects.exclude(username="akadmin")
            .exclude(username__startswith="ak-outpost")
            .exclude_anonymous()
            .exclude(pk=self.user.pk)
            .first()
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
    def test_idp_post_auto(self):
        """test SAML Source With post binding (auto redirect)"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        pre_authentication_flow = Flow.objects.get(slug="default-source-pre-authentication")
        keypair = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=IDP_CERT,
            key_data=IDP_KEY,
        )

        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=self.slug,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            pre_authentication_flow=pre_authentication_flow,
            issuer="entity-id",
            sso_url=f"http://{self.host}:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.POST_AUTO,
            signing_kp=keypair,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()

        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait_for_url(self.if_user_url())

        self.assert_user(
            User.objects.exclude(username="akadmin")
            .exclude(username__startswith="ak-outpost")
            .exclude_anonymous()
            .exclude(pk=self.user.pk)
            .first()
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
    def test_idp_post_auto_enroll_auth(self):
        """test SAML Source With post binding (auto redirect)"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")
        pre_authentication_flow = Flow.objects.get(slug="default-source-pre-authentication")
        keypair = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=IDP_CERT,
            key_data=IDP_KEY,
        )

        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=self.slug,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            pre_authentication_flow=pre_authentication_flow,
            issuer="entity-id",
            sso_url=f"http://{self.host}:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.POST_AUTO,
            signing_kp=keypair,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()

        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait_for_url(self.if_user_url())

        self.assert_user(
            User.objects.exclude(username="akadmin")
            .exclude(username__startswith="ak-outpost")
            .exclude_anonymous()
            .exclude(pk=self.user.pk)
            .first()
        )

        # Clear all cookies and log in again
        self.driver.delete_all_cookies()
        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()

        # Now we should be at the IDP, wait for the username field
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("user1pass")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait_for_url(self.if_user_url())

        # sleep(999999)
        self.assert_user(
            User.objects.exclude(username="akadmin")
            .exclude(username__startswith="ak-outpost")
            .exclude_anonymous()
            .exclude(pk=self.user.pk)
            .first()
        )
