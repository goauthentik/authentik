from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.enterprise.requests.models import Persona


class PersonaTests(APITestCase):

    def _grant_create_perm(self, user):
        user.assign_perms_to_managed_role("authentik_requests.add_persona")

    def test_create_requires_permission(self):
        """Ordinary users cannot create personas -- admin-provisioned, not
        self-service"""
        user = create_test_user()
        other_user = create_test_user()
        self.client.force_login(user)

        res = self.client.post(
            reverse("authentik_api:persona-list"),
            data={"parent": other_user.pk},
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_creates_persona_for_user(self):
        """An admin with add_persona can create a persona for any user"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        other_user = create_test_user()
        self.client.force_login(admin)

        res = self.client.post(
            reverse("authentik_api:persona-list"),
            data={"parent": other_user.pk, "label": "support-bot"},
        )
        self.assertEqual(res.status_code, 201, res.content)
        persona = Persona.objects.get(parent=other_user)
        self.assertTrue(persona.username.startswith("persona-"))
        self.assertEqual(persona.name, "support-bot")

    def test_persona_defaults_to_non_expiring(self):
        """A persona created without an explicit expiry is a standing identity"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        other_user = create_test_user()
        self.client.force_login(admin)

        res = self.client.post(
            reverse("authentik_api:persona-list"),
            data={"parent": other_user.pk},
        )
        self.assertEqual(res.status_code, 201, res.content)
        persona = Persona.objects.get(parent=other_user)
        self.assertFalse(persona.expiring)
        self.assertIsNone(persona.expires)

    def test_list_only_shows_own_personas(self):
        """A user only sees personas they have object-level permission on
        (granted automatically to the parent at creation time)"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        user = create_test_user()
        other_user = create_test_user()
        self.client.force_login(admin)

        self.client.post(
            reverse("authentik_api:persona-list"),
            data={"parent": other_user.pk},
        )
        res = self.client.post(
            reverse("authentik_api:persona-list"),
            data={"parent": user.pk},
        )
        self.assertEqual(res.status_code, 201, res.content)

        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:persona-list"))
        content = res.json()
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(content["results"][0]["parent"]["pk"], user.pk)

    def test_destroy_own_persona(self):
        user = create_test_user()
        self.client.force_login(user)
        persona = Persona.create_for_user(user)
        user.assign_perms_to_managed_role(
            ["authentik_requests.view_persona", "authentik_requests.delete_persona"], persona
        )

        res = self.client.delete(reverse("authentik_api:persona-detail", kwargs={"pk": persona.pk}))
        self.assertEqual(res.status_code, 204, res.content)
        self.assertFalse(Persona.objects.filter(pk=persona.pk).exists())

    def test_deleting_parent_cascades_to_persona(self):
        """Deleting the parent user deletes their personas along with it"""
        user = create_test_user()
        persona = Persona.create_for_user(user)
        persona_pk = persona.pk

        user.delete()
        self.assertFalse(Persona.objects.filter(pk=persona_pk).exists())
