"""email tests"""

from unittest.mock import PropertyMock, patch

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
from authentik.lib.generators import generate_id
from authentik.stages.email.models import EmailStage, EmailTemplate
from authentik.stages.email.utils import TemplateEmailMessage


class TestEmailStageTemplates(FlowTestCase):
    """Email tests"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = EmailStage.objects.create(
            name="email",
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_custom_template_invalid_syntax(self):
        """Test with custom template"""
        self.stage.template = EmailTemplate.objects.create(
            path="invalid.html", body="{% blocktranslate %}"
        )
        self.stage.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
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

    def test_template_name_relative(self):
        """Test template names are normalized before lookup"""
        template = EmailTemplate.objects.create(path=f"{generate_id()}.html", body="body")
        message = TemplateEmailMessage(to=[("", "foo@bar.baz")], template_name=f"./{template.path}")
        self.assertEqual(message.alternatives[0][0], "body")
