"""Test Application Entitlements API"""

from rest_framework.test import APITestCase

from authentik.core.models import Application, ApplicationEntitlement, Group
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
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
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, user=self.other_user, order=0)

    def test_user(self):
        """Test user-direct assignment"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, user=self.user, order=0)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_group(self):
        """Test direct group"""
        group = Group.objects.create(name=generate_id())
        self.user.ak_groups.add(group)
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, group=group, order=0)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_group_indirect(self):
        """Test indirect group"""
        parent = Group.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id(), parent=parent)
        self.user.ak_groups.add(group)
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, group=parent, order=0)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)
