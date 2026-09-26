"""RAC e2e tests"""

from time import sleep

from docker.models.containers import Container
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.endpoints.connectors.agent.models import AgentConnector, EnrollmentToken
from authentik.endpoints.models import Device
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.rac.models import Protocols, RACProvider, agent_ssh_host_key
from authentik.providers.rac.tests import create_test_device
from tests.decorators import retry
from tests.selenium import ChannelsSeleniumTestCase

ENROLLMENT_KEY = "test-enroll-key"  # nosec


class TestProviderRAC(ChannelsSeleniumTestCase):
    """RAC e2e tests"""

    def setUp(self):
        super().setUp()
        self.password = generate_id()

    def join_domain(self, machine: Container):
        """Enroll a machine with authentik, as a user would. The agent is started by
        the machine itself, so this waits for it to come up."""
        output = b""
        for _ in range(20):
            code, output = machine.exec_run(
                f"ak-sysd domains join ak -a {self.live_server_url}",
                environment={"AK_SYS_INSECURE_ENV_TOKEN": ENROLLMENT_KEY},
            )
            if code == 0:
                return
            sleep(3)
        self.fail(f"failed to enroll machine: {output}")

    def start_rac(self, outpost: Outpost):
        """Start rac container based on outpost created"""
        self.run_container(
            image=self.get_container_image("ghcr.io/goauthentik/dev-rac"),
            environment={
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
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
        test_ssh = self.run_container(
            image=self.pinned_image("openssh-server", "e2e/compose.yml"),
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
            delete_token_on_disconnect=True,
            settings={
                "username": "authentik",
                "password": self.password,
            },
        )
        device = create_test_device(host=f"{self.host}:2222", protocol=Protocols.SSH)
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=rac)
        outpost: Outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.RAC,
        )
        outpost.providers.add(rac)
        outpost.build_user_permissions(outpost.user)

        self.start_rac(outpost)

        self.driver.get(
            self.url(
                "authentik_providers_rac:start",
                app=app.slug,
                device=device.pk,
                protocol=Protocols.SSH,
            )
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

    def enroll_agent(self) -> tuple[Device, Container]:
        """Run a machine with the authentik agent and enroll it, as a user would"""
        connector = AgentConnector.objects.create(name=generate_id())
        EnrollmentToken.objects.create(name=generate_id(), key=ENROLLMENT_KEY, connector=connector)
        name = f"device-{generate_id(10)}"
        machine = self.run_container(
            # Brings sshd and the agent, which validates authentik's certificates
            image=self.pinned_image("platform-ssh", "e2e/compose.yml"),
            name=name,
            hostname=name,
        )
        # The machine resolves users locally, it has no connection to a directory.
        # Usernames of authentik users are not restricted the way local ones are.
        code, output = machine.exec_run(
            f"sh -c 'useradd -m -s /bin/bash {self.user.username} "
            f"|| useradd -m -s /bin/bash --badname {self.user.username}'"
        )
        self.assertEqual(code, 0, output)
        self.join_domain(machine)
        # The agent reports the host keys of its device once it has enrolled, which is
        # what authentik connects to it with
        for _ in range(30):
            device = Device.objects.filter(deviceconnection__connector=connector).first()
            if device and agent_ssh_host_key(device):
                return device, machine
            sleep(2)
        raise TimeoutError("device did not report its SSH host keys")

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
    def test_rac_ssh_certificate(self):
        """Test SSH RAC to a device managed by the authentik agent, which is logged
        into as the authentik user with a certificate instead of credentials"""
        device, machine = self.enroll_agent()

        rac: RACProvider = RACProvider.objects.create(
            name=generate_id(),
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            delete_token_on_disconnect=True,
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=rac)
        outpost: Outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.RAC,
        )
        outpost.providers.add(rac)
        outpost.build_user_permissions(outpost.user)

        self.start_rac(outpost)

        # The device is connected to with what it reported about itself, there are no
        # credentials and no settings anywhere
        self.driver.get(
            self.url(
                "authentik_providers_rac:start",
                app=app.slug,
                device=device.pk,
                protocol=Protocols.SSH,
            )
        )
        self.login()
        sleep(1)

        iface = self.driver.find_element(By.CSS_SELECTOR, "ak-rac")
        sleep(5)
        state = self.driver.execute_script("return arguments[0].clientState", iface)
        self.assertEqual(state, 3)

        # Being logged in as the authentik user means the certificate authenticated it
        uid = generate_id()
        self.driver.find_element(By.CSS_SELECTOR, "body").send_keys(
            f"whoami > /tmp/{uid}" + Keys.ENTER
        )

        sleep(2)

        _, output = machine.exec_run(f"cat /tmp/{uid}")
        self.assertEqual(output.decode().strip(), self.user.username)
