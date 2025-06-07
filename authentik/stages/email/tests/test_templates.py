"""email tests"""

from os import chmod, unlink
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from typing import Any
from unittest.mock import PropertyMock, patch

from django.conf import settings
from django.core.mail.backends.locmem import EmailBackend
from django.core.mail.message import sanitize_address
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.email.models import EmailStage, get_template_choices
from authentik.stages.email.utils import TemplateEmailMessage


def get_templates_setting(temp_dir: str) -> dict[str, Any]:
    """Patch settings TEMPLATE's dir property"""
    templates_setting = settings.TEMPLATES
    templates_setting[0]["DIRS"] = [temp_dir, "foo"]
    return templates_setting


class TestEmailStageTemplates(FlowTestCase):
    """Email tests"""

    def setUp(self) -> None:
        self.dir = Path(mkdtemp())
        self.user = create_test_admin_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = EmailStage.objects.create(
            name="email",
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def tearDown(self) -> None:
        rmtree(self.dir)

    def test_custom_template(self):
        """Test with custom template"""
        with self.settings(TEMPLATES=get_templates_setting(self.dir)):
            _, file = mkstemp(suffix=".html", dir=self.dir)
            _, file2 = mkstemp(suffix=".html", dir=self.dir)
            chmod(file2, 0o000)  # Remove all permissions so we can't read the file
            choices = get_template_choices()
            self.assertEqual(choices[-1][0], Path(file).name)
            self.assertEqual(len(choices), 3)
            unlink(file)
            unlink(file2)

    def test_custom_template_invalid_syntax(self):
        """Test with custom template"""
        with open(self.dir / Path("invalid.html"), "w+", encoding="utf-8") as _invalid:
            _invalid.write("{% blocktranslate %}")
        with self.settings(TEMPLATES=get_templates_setting(self.dir)):
            self.stage.template = "invalid.html"
            plan = FlowPlan(
                flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()]
            )
            plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
            session = self.client.session
            session[SESSION_KEY_PLAN] = plan
            session.save()

            url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            with patch(
                "authentik.stages.email.models.EmailStage.backend_class",
                PropertyMock(return_value=EmailBackend),
            ):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertStageResponse(
                    response,
                    self.flow,
                    error_message="Unknown error",
                )
                events = Event.objects.filter(action=EventAction.CONFIGURATION_ERROR)
                self.assertEqual(len(events), 1)
                event = events.first()
                self.assertEqual(
                    event.context["message"], "Exception occurred while rendering E-mail template"
                )
                self.assertEqual(event.context["template"], "invalid.html")

    def test_template_address(self):
        """Test addresses are correctly parsed"""
        message = TemplateEmailMessage(to=[("foo@bar.baz", "foo@bar.baz")])
        [sanitize_address(addr, "utf-8") for addr in message.recipients()]
        self.assertEqual(message.recipients(), ['"foo@bar.baz" <foo@bar.baz>'])
        message = TemplateEmailMessage(to=[("some-name", "foo@bar.baz")])
        [sanitize_address(addr, "utf-8") for addr in message.recipients()]
        self.assertEqual(message.recipients(), ["some-name <foo@bar.baz>"])
