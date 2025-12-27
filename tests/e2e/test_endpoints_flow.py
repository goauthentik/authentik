"""test default login flow"""

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AgentConnector, EnrollmentToken
from authentik.endpoints.models import Device, EndpointStage, StageMode
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, FlowStageBinding
from authentik.lib.generators import generate_id
from tests.e2e.utils import SeleniumTestCase, retry


class TestEndpointsFlow(SeleniumTestCase):
    """test default login flow"""

    @reconcile_app("authentik_crypto")
    def setUp(self):
        super().setUp()
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
            challenge_key=CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first(),
        )
        self.enrollment_token = EnrollmentToken.objects.create(
            name=generate_id(), connector=self.connector
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_login(self):
        """test default login flow"""
        rc, output = self.driver_container.exec_run(
            ["ak-sysd", "domains", "join", "ak", "-a", self.live_server_url],
            user="root",
            environment={"AK_SYS_INSECURE_ENV_TOKEN": self.enrollment_token.key},
        )
        self.assertEqual(rc, 0, str(output))

        dev = Device.objects.filter(name="docker-desktop").first()
        self.assertIsNotNone(dev)

        stage = EndpointStage.objects.create(
            name=generate_id(), connector=self.connector, mode=StageMode.REQUIRED
        )
        FlowStageBinding.objects.create(
            target=Flow.objects.get(slug="default-authentication-flow"), stage=stage, order=0
        )

        self.driver.get(
            self.url(
                "authentik_core:if-flow",
                flow_slug="default-authentication-flow",
            )
        )
        self.login()
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)

        login_evt = Event.objects.filter(action=EventAction.LOGIN).first()
        self.assertIsNotNone(login_evt)
        self.assertEqual(login_evt.context["device"]["pk"], dev.pk.hex)
