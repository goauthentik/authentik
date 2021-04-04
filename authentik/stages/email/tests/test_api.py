"""email stage api tests"""
from django.urls import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.stages.email.api import EmailStageSerializer
from authentik.stages.email.models import EmailTemplates


class TestEmailStageAPI(APITestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.akadmin = User.objects.get(username="akadmin")
        self.client.force_login(self.akadmin)

    def test_templates(self):
        """Test template list"""
        response = self.client.get(reverse("authentik_api:emailstage-templates"))
        self.assertEqual(response.status_code, 200)

    def test_validate(self):
        """Test EmailStage's validation"""
        self.assertEqual(
            # pyright: reportGeneralTypeIssues=false
            EmailStageSerializer().validate_template(EmailTemplates.ACCOUNT_CONFIRM),
            EmailTemplates.ACCOUNT_CONFIRM,
        )
        with self.assertRaises(ValidationError):
            print(EmailStageSerializer().validate_template("foobar"))
