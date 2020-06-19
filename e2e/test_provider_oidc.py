"""test OpenID Provider flow"""
from time import sleep

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from oauth2_provider.generators import generate_client_id, generate_client_secret
from oidc_provider.models import Client, ResponseType
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types import Healthcheck
from e2e.utils import apply_default_data, ensure_rsa_key
from passbook.core.models import Application
from passbook.flows.models import Flow
from passbook.providers.oidc.models import OpenIDProvider


class TestProviderOIDC(StaticLiveServerTestCase):
    """test OpenID Provider flow"""

    def setUp(self):
        self.driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.CHROME,
        )
        self.driver.implicitly_wait(5)
        apply_default_data()
        self.client_id = generate_client_id()
        self.client_secret = generate_client_secret()
        self.container = self.setup_client()

    def setup_client(self) -> Container:
        """Setup client grafana container which we test OIDC against"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="grafana/grafana:latest",
            detach=True,
            name=f"passbook-e2e-grafana-client_{self.port}",
            network_mode="host",
            auto_remove=True,
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:3000"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
            environment={
                "GF_AUTH_GENERIC_OAUTH_ENABLED": "true",
                "GF_AUTH_GENERIC_OAUTH_CLIENT_ID": self.client_id,
                "GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET": self.client_secret,
                "GF_AUTH_GENERIC_OAUTH_SCOPES": "openid email profile",
                "GF_AUTH_GENERIC_OAUTH_AUTH_URL": (
                    f"{self.live_server_url}/application/oidc/authorize"
                ),
                "GF_AUTH_GENERIC_OAUTH_TOKEN_URL": (
                    f"{self.live_server_url}/application/oidc/token"
                ),
                "GF_AUTH_GENERIC_OAUTH_API_URL": (
                    f"{self.live_server_url}/application/oidc/userinfo"
                ),
                "GF_LOG_LEVEL": "debug",
            },
        )
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            sleep(1)

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.container.kill()

    def test_redirect_uri_error(self):
        """test OpenID Provider flow (invalid redirect URI, check error message)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(slug="default-provider-authorization")
        client = Client.objects.create(
            name="grafana",
            client_type="confidential",
            client_id=self.client_id,
            client_secret=self.client_secret,
            _redirect_uris="http://localhost:3000/",
            _scope="openid userinfo",
        )
        # At least one of these objects must exist
        ensure_rsa_key()
        # This response_code object might exist or not, depending on the order the tests are run
        rp_type, _ = ResponseType.objects.get_or_create(value="code")
        client.response_types.set([rp_type])
        client.save()
        provider = OpenIDProvider.objects.create(
            oidc_client=client, authorization_flow=authorization_flow,
        )
        Application.objects.create(
            name="Grafana", slug="grafana", provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        sleep(2)
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "pf-c-title").text,
            "Redirect URI Error",
        )

    def test_authorization_no_consent(self):
        """test OpenID Provider flow (default authorization flow without consent)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(slug="default-provider-authorization")
        client = Client.objects.create(
            name="grafana",
            client_type="confidential",
            client_id=self.client_id,
            client_secret=self.client_secret,
            _redirect_uris="http://localhost:3000/login/generic_oauth",
            _scope="openid profile email",
            reuse_consent=False,
            require_consent=False,
        )
        # At least one of these objects must exist
        ensure_rsa_key()
        # This response_code object might exist or not, depending on the order the tests are run
        rp_type, _ = ResponseType.objects.get_or_create(value="code")
        client.response_types.set([rp_type])
        client.save()
        provider = OpenIDProvider.objects.create(
            oidc_client=client, authorization_flow=authorization_flow,
        )
        Application.objects.create(
            name="Grafana", slug="grafana", provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/profile')]").click()
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "page-header__title").text,
            "passbook Default Admin",
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[1]/div/input",
            ).get_attribute("value"),
            "passbook Default Admin",
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[2]/div/input",
            ).get_attribute("value"),
            "root@localhost",
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[3]/div/input",
            ).get_attribute("value"),
            "root@localhost",
        )

    def test_authorization_consent(self):
        """test OpenID Provider flow (default authorization flow with consent)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-consent"
        )
        client = Client.objects.create(
            name="grafana",
            client_type="confidential",
            client_id=self.client_id,
            client_secret=self.client_secret,
            _redirect_uris="http://localhost:3000/login/generic_oauth",
            _scope="openid profile email",
            reuse_consent=False,
            require_consent=False,
        )
        # At least one of these objects must exist
        ensure_rsa_key()
        # This response_code object might exist or not, depending on the order the tests are run
        rp_type, _ = ResponseType.objects.get_or_create(value="code")
        client.response_types.set([rp_type])
        client.save()
        provider = OpenIDProvider.objects.create(
            oidc_client=client, authorization_flow=authorization_flow,
        )
        app = Application.objects.create(
            name="Grafana", slug="grafana", provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        self.assertIn(
            app.name,
            self.driver.find_element(
                By.XPATH, "/html/body/div[2]/div/main/div/form/div[2]/p[1]"
            ).text,
        )
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()

        self.driver.find_element(By.XPATH, "//a[contains(@href, '/profile')]").click()
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "page-header__title").text,
            "passbook Default Admin",
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[1]/div/input",
            ).get_attribute("value"),
            "passbook Default Admin",
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[2]/div/input",
            ).get_attribute("value"),
            "root@localhost",
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[3]/div/input",
            ).get_attribute("value"),
            "root@localhost",
        )
