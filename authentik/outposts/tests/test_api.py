"""Test outpost service connection API"""

from unittest.mock import patch

from django.urls import reverse
from dramatiq import actor, get_broker
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import PropertyMapping, Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.outposts.api.outposts import OutpostSerializer
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost, OutpostType, default_outpost_config
from authentik.outposts.tasks import CACHE_KEY_OUTPOST_DOWN
from authentik.providers.ldap.models import LDAPProvider
from authentik.providers.proxy.models import ProxyProvider
from authentik.tasks.models import Task, TaskLog


class TestOutpostServiceConnectionsAPI(APITestCase):
    """Test outpost service connection API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name=generate_id(), expression="""return {'foo': 'bar'}"""
        )
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    @reconcile_app("authentik_outposts")
    def test_managed_name_change(self):
        """Test name change for embedded outpost"""
        embedded_outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        self.assertIsNotNone(embedded_outpost)
        response = self.client.patch(
            reverse("authentik_api:outpost-detail", kwargs={"pk": embedded_outpost.pk}),
            {"name": "foo"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content, {"name": ["Embedded outpost's name cannot be changed"]}
        )

    @reconcile_app("authentik_outposts")
    def test_managed_without_managed(self):
        """Test name change for embedded outpost"""
        embedded_outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        self.assertIsNotNone(embedded_outpost)
        embedded_outpost.managed = ""
        embedded_outpost.save()
        response = self.client.patch(
            reverse("authentik_api:outpost-detail", kwargs={"pk": embedded_outpost.pk}),
            {"name": "foo"},
        )
        self.assertEqual(response.status_code, 200)
        embedded_outpost.refresh_from_db()
        self.assertEqual(embedded_outpost.managed, MANAGED_OUTPOST)

    def test_outpost_validation(self):
        """Test Outpost validation"""
        valid = OutpostSerializer(
            data={
                "name": generate_id(),
                "type": OutpostType.PROXY,
                "config": default_outpost_config(),
                "providers": [
                    ProxyProvider.objects.create(
                        name=generate_id(), authorization_flow=create_test_flow()
                    ).pk
                ],
            }
        )
        self.assertTrue(valid.is_valid())
        invalid = OutpostSerializer(
            data={
                "name": generate_id(),
                "type": OutpostType.PROXY,
                "config": default_outpost_config(),
                "providers": [
                    LDAPProvider.objects.create(
                        name=generate_id(), authorization_flow=create_test_flow()
                    ).pk
                ],
            }
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("providers", invalid.errors)

    def test_types(self):
        """Test OutpostServiceConnections's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:outpostserviceconnection-types"),
        )
        self.assertEqual(response.status_code, 200)

    def test_outpost_config(self):
        """Test Outpost's config field"""
        provider = ProxyProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        invalid = OutpostSerializer(
            data={"name": generate_id(), "providers": [provider.pk], "config": ""}
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("config", invalid.errors)
        valid = OutpostSerializer(
            data={
                "name": generate_id(),
                "providers": [provider.pk],
                "config": default_outpost_config(generate_id()),
                "type": OutpostType.PROXY,
            }
        )
        self.assertTrue(valid.is_valid())

    @patch("authentik.tenants.utils.get_install_id", return_value="test-install-id")
    def test_delete_outpost_with_live_side_effects(self, _get_install_id):
        """Test deleting an outpost when scheduled-model side effects are enabled."""
        self.client.logout()
        token = Token.objects.create(user=self.user, intent=TokenIntents.INTENT_API, expiring=False)
        provider_1 = ProxyProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        provider_2 = ProxyProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        with self.settings(TEST=False):
            outpost = Outpost.objects.create(
                name=generate_id(),
                type=OutpostType.PROXY,
                _config=default_outpost_config(),
            )
            outpost.providers.set([provider_1, provider_2])

            response = self.client.delete(
                reverse("authentik_api:outpost-detail", kwargs={"pk": outpost.pk}),
                HTTP_AUTHORIZATION=f"Bearer {token.key}",
            )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Outpost.objects.filter(pk=outpost.pk).exists())

    def test_delete_outpost_without_service_account(self):
        """Test deleting an outpost doesn't recreate a missing service account."""
        outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.PROXY,
            _config=default_outpost_config(),
        )
        outpost.service_account.delete()

        with patch("authentik.outposts.models.User.objects.create") as user_create:
            outpost.delete()

        user_create.assert_not_called()

    @patch("authentik.outposts.signals.cache.set")
    @patch("authentik.outposts.signals.outpost_controller.send_with_options")
    def test_delete_outpost_keeps_task_logs(self, _controller_send, _cache_set):
        """Test outpost deletion doesn't cascade to task history."""

        @actor
        def test_task():
            pass

        outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.PROXY,
            _config=default_outpost_config(),
        )
        test_task.send_with_options(rel_obj=outpost)
        task = Task.objects.get(actor_name=test_task.actor_name)

        outpost.delete()

        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.assertGreater(TaskLog.objects.filter(task=task).count(), 0)
        broker = get_broker()
        del broker.actors[test_task.actor_name]

    @patch("authentik.outposts.signals.cache.set")
    @patch("authentik.outposts.signals.outpost_controller.send_with_options")
    def test_delete_outpost_schedules_teardown_after_commit(self, controller_send, cache_set):
        """Test outpost teardown is deferred until the delete commits."""
        outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.PROXY,
            _config=default_outpost_config(),
        )
        controller_send.reset_mock()
        cache_set.reset_mock()
        outpost_pk = outpost.pk.hex

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            outpost.delete()

        controller_send.assert_not_called()
        cache_set.assert_not_called()
        self.assertEqual(len(callbacks), 1)

        callbacks[0]()

        cache_set.assert_called_once_with(CACHE_KEY_OUTPOST_DOWN % outpost_pk, outpost)
        controller_send.assert_called_once_with(
            args=(outpost_pk,),
            kwargs={"action": "down", "from_cache": True},
            uid=outpost.name,
        )
