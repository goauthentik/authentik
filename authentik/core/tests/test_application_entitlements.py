"""Test Application Entitlements API"""


from rest_framework.test import APITestCase

from authentik.core.models import Application, ApplicationEntitlement, Group
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider


class TestApplicationEntitlements(APITestCase):
    """Test application entitlements"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.other_user = create_test_user()
        self.provider = OAuth2Provider.objects.create(
            name="test",
            redirect_uris="http://some-other-domain",
            authorization_flow=create_test_flow(),
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        ApplicationEntitlement.objects.create(
            user=self.other_user, app=self.app, name=generate_id()
        )

    def test_user(self):
        """Test user-direct assignment"""
        ent = ApplicationEntitlement.objects.create(
            user=self.user, app=self.app, name=generate_id()
        )
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_group(self):
        """Test direct group"""
        group = Group.objects.create(name=generate_id())
        self.user.ak_groups.add(group)
        ent = ApplicationEntitlement.objects.create(group=group, app=self.app, name=generate_id())
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_group_indirect(self):
        """Test indirect group"""
        parent = Group.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id(), parent=parent)
        self.user.ak_groups.add(group)
        ent = ApplicationEntitlement.objects.create(group=parent, app=self.app, name=generate_id())
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)
