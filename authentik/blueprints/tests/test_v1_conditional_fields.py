"""Test blueprints v1"""
from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import Application, Token
from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.sources.oauth.models import OAuthSource


class TestBlueprintsV1ConditionalFields(TransactionTestCase):
    """Test Blueprints conditional fields"""

    def setUp(self) -> None:
        user = create_test_admin_user()
        self.uid = generate_id()
        import_yaml = load_fixture("fixtures/conditional_fields.yaml", uid=self.uid, user=user.pk)

        importer = Importer(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

    def test_token(self):
        """Test token"""
        token = Token.objects.filter(identifier=f"{self.uid}-token").first()
        self.assertIsNotNone(token)
        self.assertEqual(token.key, self.uid)

    def test_application(self):
        """Test application"""
        app = Application.objects.filter(slug=f"{self.uid}-app").first()
        self.assertIsNotNone(app)
        self.assertEqual(app.meta_icon, "https://goauthentik.io/img/icon.png")

    def test_source(self):
        """Test source"""
        source = OAuthSource.objects.filter(slug=f"{self.uid}-source").first()
        self.assertIsNotNone(source)
        self.assertEqual(source.icon, "https://goauthentik.io/img/icon.png")

    def test_flow(self):
        """Test flow"""
        flow = Flow.objects.filter(slug=f"{self.uid}-flow").first()
        self.assertIsNotNone(flow)
        self.assertEqual(flow.background, "https://goauthentik.io/img/icon.png")
