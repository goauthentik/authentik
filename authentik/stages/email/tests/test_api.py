"""email stage api tests"""

from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.stages.email.api import EmailStageSerializer
from authentik.stages.email.models import EmailTemplate


class TestEmailStageAPI(APITestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_validate(self):
        """Test EmailStage's validation"""

        template = EmailTemplate.objects.get(managed="goauthentik.io/email/account-confirmation")
        serializer = EmailStageSerializer(
            data={
                "name": generate_id(),
                "template": template.pk,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["template"], template)

        serializer = EmailStageSerializer(
            data={
                "name": generate_id(),
                "template": None,
            },
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("template", serializer.errors)
