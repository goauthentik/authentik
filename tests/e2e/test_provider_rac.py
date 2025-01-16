"""RAC e2e tests"""

from datetime import timedelta
from time import mktime, sleep
from unittest.mock import MagicMock, patch

from django.utils.timezone import now
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import License
from authentik.enterprise.providers.rac.models import Endpoint, Protocols, RACProvider
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from tests.e2e.utils import SeleniumTestCase, retry


class TestProviderRAC(SeleniumTestCase):
    """RAC e2e tests"""

    def setUp(self):
        super().setUp()
        self.password = generate_id()

    def start_rac(self, outpost: Outpost):
        """Start rac container based on outpost created"""
        self.run_container(
            image=self.get_container_image("ghcr.io/goauthentik/dev-rac"),
            environment={
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
        )

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=int(mktime((now() + timedelta(days=3000)).timetuple())),
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
        "default/flow-default-provider-invalidation.yaml",
    )
    @apply_blueprint(
        "system/providers-rac.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_rac_ssh(self):
        """Test SSH RAC"""
        License.objects.create(key=generate_id())

        test_ssh = self.run_container(
            image="lscr.io/linuxserver/openssh-server:latest",
            ports={
                "2222": "2222",
            },
            environment={
                "USER_NAME": "authentik",
                "USER_PASSWORD": self.password,
                "PASSWORD_ACCESS": "true",
                "SUDO_ACCESS": "true",
            },
        )

        rac: RACProvider = RACProvider.objects.create(
            name=generate_id(),
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
        )
        endpoint = Endpoint.objects.create(
            name=generate_id(),
            protocol=Protocols.SSH,
            host=f"{self.host}:2222",
            settings={
                "username": "authentik",
                "password": self.password,
            },
            provider=rac,
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=rac)
        outpost: Outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.RAC,
        )
        outpost.providers.add(rac)
        outpost.build_user_permissions(outpost.user)

        self.start_rac(outpost)
        self.wait_for_outpost(outpost)

        self.driver.get(
            self.url("authentik_providers_rac:start", app=app.slug, endpoint=endpoint.pk)
        )
        self.login()
        sleep(1)

        iface = self.driver.find_element(By.CSS_SELECTOR, "ak-rac")
        sleep(5)
        state = self.driver.execute_script("return arguments[0].clientState", iface)
        self.assertEqual(state, 3)

        uid = generate_id()
        self.driver.find_element(By.CSS_SELECTOR, "body").send_keys(
            f'echo "{uid}" > /tmp/test' + Keys.ENTER
        )

        sleep(2)

        _, output = test_ssh.exec_run("cat /tmp/test")
        self.assertEqual(output, f"{uid}\n".encode())
