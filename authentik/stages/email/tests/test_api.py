"""email stage api tests"""
from django.urls import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.stages.email.api import EmailStageSerializer
from authentik.stages.email.models import EmailTemplates


class TestEmailStageAPI(APITestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_templates(self):
        """Test template list"""
        response = self.client.get(reverse("authentik_api:emailstage-templates"))
        self.assertEqual(response.status_code, 200)

    def test_validate(self):
        """Test EmailStage's validation"""
        self.assertEqual(
            EmailStageSerializer().validate_template(EmailTemplates.ACCOUNT_CONFIRM),
            EmailTemplates.ACCOUNT_CONFIRM,
        )
        with self.assertRaises(ValidationError):
            EmailStageSerializer().validate_template("foobar")
