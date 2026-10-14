"""outpost tests"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.apps import apps
from django.contrib.auth.management import create_permissions
from django.db import close_old_connections, transaction
from django.test import TestCase, TransactionTestCase

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider


class OutpostTests(TestCase):
    """Outpost Tests"""

    def setUp(self) -> None:
        create_permissions(apps.get_app_config("authentik_outposts"))
        return super().setUp()

    def test_service_account_permissions(self):
        """Test that the service account has correct permissions"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=create_test_flow(),
        )
        outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
        )

        # Before we add a provider, the user should only have access to the outpost
        permissions = outpost.user.get_all_obj_perms_on_managed_role()
        self.assertEqual(len(permissions), 1)
        self.assertEqual(permissions[0].object_pk, str(outpost.pk))

        # We add a provider, user should only have access to outpost and provider
        outpost.providers.add(provider)
        provider.refresh_from_db()
        permissions = outpost.user.get_all_obj_perms_on_managed_role().order_by(
            "content_type__model"
        )
        self.assertEqual(len(permissions), 2)
        self.assertEqual(permissions[0].object_pk, str(outpost.pk))
        self.assertEqual(permissions[1].object_pk, str(provider.pk))

        # Provider requires a certificate-key-pair, user should have permissions for it
        keypair = create_test_cert()
        provider.certificate = keypair
        provider.save()
        permissions = outpost.user.get_all_obj_perms_on_managed_role().order_by(
            "content_type__model"
        )
        self.assertEqual(len(permissions), 5)
        self.assertEqual(permissions[0].object_pk, str(keypair.pk))
        self.assertEqual(permissions[1].object_pk, str(keypair.pk))
        self.assertEqual(permissions[2].object_pk, str(keypair.pk))
        self.assertEqual(permissions[3].object_pk, str(outpost.pk))
        self.assertEqual(permissions[4].object_pk, str(provider.pk))

        # Remove provider from outpost, user should only have access to outpost
        outpost.providers.remove(provider)
        permissions = outpost.user.get_all_obj_perms_on_managed_role()
        self.assertEqual(len(permissions), 1)
        self.assertEqual(permissions[0].object_pk, str(outpost.pk))

    def test_service_account_permissions_unchanged(self):
        """Test that saving a provider without changes keeps the existing permission rows"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=create_test_flow(),
            certificate=create_test_cert(),
        )
        outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
        )
        outpost.providers.add(provider)
        user = outpost.user
        # A permission the outpost doesn't need is removed
        user.assign_perms_to_managed_role("authentik_core.view_user", user)
        user.assign_perms_to_managed_role("authentik_core.view_user")
        provider.save()
        rows = set(user.get_all_obj_perms_on_managed_role().values_list("pk", flat=True))
        model_rows = set(user.get_all_model_perms_on_managed_role().values_list("pk", flat=True))
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(model_rows), 1)

        provider.save()
        self.assertEqual(
            set(user.get_all_obj_perms_on_managed_role().values_list("pk", flat=True)), rows
        )
        self.assertEqual(
            set(user.get_all_model_perms_on_managed_role().values_list("pk", flat=True)),
            model_rows,
        )


class OutpostPermissionConcurrencyTests(TransactionTestCase):
    """Outpost permission tests across concurrent transactions"""

    def test_concurrent_provider_saves(self):
        """Test that providers of one outpost can be saved in parallel transactions,
        as parallel blueprint applies do"""
        create_permissions(apps.get_app_config("authentik_outposts"))
        flow = create_test_flow()
        keypair = create_test_cert()
        providers = [
            ProxyProvider.objects.create(
                name=f"test-{i}",
                internal_host="http://localhost",
                external_host=f"http://test-{i}.localhost",
                authorization_flow=flow,
                certificate=keypair,
            )
            for i in range(30)
        ]
        outpost: Outpost = Outpost.objects.create(name="test", type=OutpostType.PROXY)
        outpost.providers.set(providers)
        workers = 4
        barrier = Barrier(workers)

        def save_providers(chunk: list[ProxyProvider]):
            close_old_connections()
            try:
                barrier.wait()
                for _ in range(3):
                    with transaction.atomic():
                        for provider in chunk:
                            ProxyProvider.objects.get(pk=provider.pk).save()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(save_providers, providers[i::workers]) for i in range(workers)
            ]
            for future in futures:
                future.result()
        # Outpost, its providers and three permissions on the shared keypair
        self.assertEqual(outpost.user.get_all_obj_perms_on_managed_role().count(), 34)
