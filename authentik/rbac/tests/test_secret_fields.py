"""Test secret field exposure in API responses"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role
from authentik.sources.plex.models import PlexSource


class TestSecretFields(APITestCase):
    """Test that secret fields are only rendered for users that can change the object"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

        PlexSource.objects.all().delete()
        self.plex_token = generate_id()
        self.source = PlexSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            plex_token=self.plex_token,
        )

    def test_source_detail_view(self):
        """Test source detail (role has global view permission)"""
        self.role.assign_perms("authentik_sources_plex.view_plexsource")
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:plexsource-detail", kwargs={"slug": self.source.slug})
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("plex_token", body)
        self.assertEqual(body["client_id"], self.source.client_id)

    def test_source_list_view(self):
        """Test source list (role has global view permission)"""
        self.role.assign_perms("authentik_sources_plex.view_plexsource")
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:plexsource-list"))
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)
        self.assertNotIn("plex_token", body["results"][0])
        self.assertEqual(body["results"][0]["client_id"], self.source.client_id)

    def test_source_detail_change_global(self):
        """Test source detail (role has global change permission)"""
        self.role.assign_perms(
            [
                "authentik_sources_plex.view_plexsource",
                "authentik_sources_plex.change_plexsource",
            ]
        )
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:plexsource-detail", kwargs={"slug": self.source.slug})
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["plex_token"], self.plex_token)

    def test_source_detail_change_object(self):
        """Test source detail (role has change permission on the object)"""
        self.role.assign_perms("authentik_sources_plex.view_plexsource", obj=self.source)
        self.role.assign_perms("authentik_sources_plex.change_plexsource", obj=self.source)
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:plexsource-detail", kwargs={"slug": self.source.slug})
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["plex_token"], self.plex_token)

    def test_source_detail_superuser(self):
        """Test source detail (superuser)"""
        self.client.force_login(create_test_admin_user())

        res = self.client.get(
            reverse("authentik_api:plexsource-detail", kwargs={"slug": self.source.slug})
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["plex_token"], self.plex_token)

    def test_source_create(self):
        """Test source create (role has global add permission, but no change permission)"""
        self.role.assign_perms("authentik_sources_plex.add_plexsource")
        self.client.force_login(self.user)

        name = generate_id()
        plex_token = generate_id()
        res = self.client.post(
            reverse("authentik_api:plexsource-list"),
            {
                "name": name,
                "slug": generate_id(),
                "plex_token": plex_token,
            },
        )
        self.assertEqual(res.status_code, 201)
        body = loads(res.content)
        self.assertNotIn("plex_token", body)
        source = PlexSource.objects.get(name=name)
        self.assertEqual(source.plex_token, plex_token)
