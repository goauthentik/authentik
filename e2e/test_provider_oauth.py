"""test OAuth Provider flow"""
from time import sleep

from oauth2_provider.generators import generate_client_id, generate_client_secret
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types import Healthcheck
from e2e.utils import USER, SeleniumTestCase
from passbook.core.models import Application
from passbook.flows.models import Flow
from passbook.providers.oauth.models import OAuth2Provider


class TestProviderOAuth(SeleniumTestCase):
    """test OAuth Provider flow"""

    def setUp(self):
        super().setUp()
        self.client_id = generate_client_id()
        self.client_secret = generate_client_secret()
        self.container = self.setup_client()

    def setup_client(self) -> Container:
        """Setup client grafana container which we test OAuth against"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="grafana/grafana:latest",
            detach=True,
            network_mode="host",
            auto_remove=True,
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:3000"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
            environment={
                "GF_AUTH_GITHUB_ENABLED": "true",
                "GF_AUTH_GITHUB_allow_sign_up": "true",
                "GF_AUTH_GITHUB_CLIENT_ID": self.client_id,
                "GF_AUTH_GITHUB_CLIENT_SECRET": self.client_secret,
                "GF_AUTH_GITHUB_SCOPES": "user:email,read:org",
                "GF_AUTH_GITHUB_AUTH_URL": self.url(
                    "passbook_providers_oauth:github-authorize"
                ),
                "GF_AUTH_GITHUB_TOKEN_URL": self.url(
                    "passbook_providers_oauth:github-access-token"
                ),
                "GF_AUTH_GITHUB_API_URL": self.url(
                    "passbook_providers_oauth:github-user"
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
        self.container.kill()
        super().tearDown()

    def test_authorization_consent_implied(self):
        """test OAuth Provider flow (default authorization flow with implied consent)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name="grafana",
            client_type=OAuth2Provider.CLIENT_CONFIDENTIAL,
            authorization_grant_type=OAuth2Provider.GRANT_AUTHORIZATION_CODE,
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uris="http://localhost:3000/login/github",
            skip_authorization=True,
            authorization_flow=authorization_flow,
        )
        Application.objects.create(
            name="Grafana", slug="grafana", provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--github").click()
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/profile')]").click()
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "page-header__title").text,
            USER().username,
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[1]/div/input",
            ).get_attribute("value"),
            USER().username,
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[2]/div/input",
            ).get_attribute("value"),
            USER().email,
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[3]/div/input",
            ).get_attribute("value"),
            USER().username,
        )

    def test_authorization_consent_explicit(self):
        """test OAuth Provider flow (default authorization flow with explicit consent)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-explicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name="grafana",
            client_type=OAuth2Provider.CLIENT_CONFIDENTIAL,
            authorization_grant_type=OAuth2Provider.GRANT_AUTHORIZATION_CODE,
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uris="http://localhost:3000/login/github",
            skip_authorization=True,
            authorization_flow=authorization_flow,
        )
        app = Application.objects.create(
            name="Grafana", slug="grafana", provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--github").click()
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        self.assertIn(
            app.name,
            self.driver.find_element(
                By.XPATH, "/html/body/div[2]/div/main/div/form/div[2]/p[1]"
            ).text,
        )
        self.assertEqual(
            "GitHub Compatibility: User Email",
            self.driver.find_element(
                By.XPATH, "/html/body/div[2]/div/main/div/form/div[2]/ul/li[1]"
            ).text,
        )
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()

        self.driver.find_element(By.XPATH, "//a[contains(@href, '/profile')]").click()
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "page-header__title").text,
            USER().username,
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[1]/div/input",
            ).get_attribute("value"),
            USER().username,
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[2]/div/input",
            ).get_attribute("value"),
            USER().email,
        )
        self.assertEqual(
            self.driver.find_element(
                By.XPATH,
                "/html/body/grafana-app/div/div/div/react-profile-wrapper/form[1]/div[3]/div/input",
            ).get_attribute("value"),
            USER().username,
        )
