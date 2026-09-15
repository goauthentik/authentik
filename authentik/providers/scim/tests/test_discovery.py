"""SCIM discovery must only adopt objects within the provider's scope."""

from django.core.cache import cache
from django.test import TestCase
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User, UserTypes
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA, SCIM_USER_SCHEMA
from authentik.providers.scim.models import (
    SCIMMapping,
    SCIMProvider,
    SCIMProviderGroup,
    SCIMProviderUser,
)
from authentik.providers.scim.tasks import scim_sync
from authentik.tenants.models import Tenant


class SCIMDiscoveryTests(TestCase):
    """Exercise discovery with real clients and provider scope filtering."""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self):
        cache.clear()
        Tenant.objects.update(avatars="none")
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.provider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            exclude_users_service_account=True,
        )
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())

    def mock_resources(self, mock: Mocker, path: str, resources: list[dict]):
        """Return a complete discovery page from a remote SCIM endpoint."""
        mock.get(
            f"https://localhost/{path}",
            json={
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(resources),
                "startIndex": 1,
                "itemsPerPage": len(resources),
                "Resources": resources,
            },
        )

    @Mocker()
    def test_discover_users_in_application_scope(self, mock: Mocker):
        """Both username and email matching must respect application access."""
        allowed = User.objects.create(username="allowed", email="allowed@example.com")
        excluded = User.objects.create(username="excluded", email="excluded@example.com")
        PolicyBinding.objects.create(target=self.app, user=allowed, order=0)
        self.app.backchannel_providers.add(self.provider)
        mock.get("https://localhost/ServiceProviderConfig", json={})

        for match_by_email in (False, True):
            with self.subTest(match_by_email=match_by_email):
                SCIMProviderUser.objects.filter(provider=self.provider).delete()
                self.mock_resources(
                    mock,
                    "Users",
                    [
                        {
                            "schemas": [SCIM_USER_SCHEMA],
                            "id": str(user.pk),
                            "userName": f"remote-{user.pk}" if match_by_email else user.username,
                            "emails": [{"value": user.email}] if match_by_email else [],
                        }
                        for user in (allowed, excluded)
                    ],
                )

                self.provider.client_for_model(User).discover()

                self.assertEqual(
                    list(
                        SCIMProviderUser.objects.filter(provider=self.provider).values_list(
                            "user_id", "scim_id"
                        )
                    ),
                    [(allowed.pk, str(allowed.pk))],
                )

    @Mocker()
    def test_discover_excluded_service_accounts(self, mock: Mocker):
        """Service-account exclusions apply even when application access is granted."""
        users = [
            User.objects.create(username=generate_id(), type=user_type)
            for user_type in (UserTypes.SERVICE_ACCOUNT, UserTypes.INTERNAL_SERVICE_ACCOUNT)
        ]
        for order, user in enumerate(users):
            PolicyBinding.objects.create(target=self.app, user=user, order=order)
        self.app.backchannel_providers.add(self.provider)
        mock.get("https://localhost/ServiceProviderConfig", json={})
        self.mock_resources(
            mock,
            "Users",
            [
                {"schemas": [SCIM_USER_SCHEMA], "id": str(user.pk), "userName": user.username}
                for user in users
            ],
        )

        self.provider.client_for_model(User).discover()

        self.assertFalse(SCIMProviderUser.objects.filter(provider=self.provider).exists())

    @Mocker(case_sensitive=True)
    def test_full_sync_adoption_and_cleanup(self, mock: Mocker):
        """Leave unmanaged excluded accounts alone, but deprovision stale managed accounts."""
        allowed_user = User.objects.create(username="allowed")
        excluded_user = User.objects.create(username="excluded")
        stale_user = User.objects.create(username="stale")
        allowed_group = Group.objects.create(name="allowed")
        excluded_group = Group.objects.create(name="excluded")
        stale_group = Group.objects.create(name="stale")
        PolicyBinding.objects.create(target=self.app, user=allowed_user, order=0)
        self.provider.group_filters.add(allowed_group)
        SCIMProviderUser.objects.create(
            provider=self.provider, user=stale_user, scim_id="stale-user"
        )
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=stale_group, scim_id="stale-group"
        )
        self.app.backchannel_providers.add(self.provider)
        mock.get("https://localhost/ServiceProviderConfig", json={})
        self.mock_resources(
            mock,
            "Users",
            [
                {"schemas": [SCIM_USER_SCHEMA], "id": remote_id, "userName": user.username}
                for user, remote_id in (
                    (allowed_user, "allowed-user"),
                    (excluded_user, "excluded-user"),
                    (stale_user, "stale-user"),
                )
            ],
        )
        self.mock_resources(
            mock,
            "Groups",
            [
                {
                    "schemas": [SCIM_GROUP_SCHEMA],
                    "id": remote_id,
                    "displayName": group.name,
                    "members": [],
                }
                for group, remote_id in (
                    (allowed_group, "allowed-group"),
                    (excluded_group, "excluded-group"),
                    (stale_group, "stale-group"),
                )
            ],
        )
        mock.put("https://localhost/Users/allowed-user", json={"id": "allowed-user"})
        mock.put("https://localhost/Groups/allowed-group", json={"id": "allowed-group"})
        mock.get(
            "https://localhost/Groups/allowed-group",
            json={"id": "allowed-group", "displayName": allowed_group.name, "members": []},
        )
        mock.delete("https://localhost/Users/stale-user", status_code=204)
        mock.delete("https://localhost/Groups/stale-group", status_code=204)

        scim_sync.send(self.provider.pk).get_result()

        self.assertEqual(
            list(
                SCIMProviderUser.objects.filter(provider=self.provider).values_list(
                    "user_id", "scim_id"
                )
            ),
            [(allowed_user.pk, "allowed-user")],
        )
        self.assertEqual(
            list(
                SCIMProviderGroup.objects.filter(provider=self.provider).values_list(
                    "group_id", "scim_id"
                )
            ),
            [(allowed_group.pk, "allowed-group")],
        )
        self.assertCountEqual(
            [
                (request.method, request.path)
                for request in mock.request_history
                if request.method != "GET"
            ],
            [
                ("PUT", "/Users/allowed-user"),
                ("PUT", "/Groups/allowed-group"),
                ("DELETE", "/Users/stale-user"),
                ("DELETE", "/Groups/stale-group"),
            ],
        )
