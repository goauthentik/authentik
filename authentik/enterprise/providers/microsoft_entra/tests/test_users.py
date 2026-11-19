"""Microsoft Entra User tests"""

from unittest.mock import AsyncMock, MagicMock, patch

from azure.identity.aio import ClientSecretCredential
from django.urls import reverse
from msgraph.generated.models.group_collection_response import GroupCollectionResponse
from msgraph.generated.models.o_data_errors.main_error import MainError
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.organization import Organization
from msgraph.generated.models.organization_collection_response import OrganizationCollectionResponse
from msgraph.generated.models.user import User as MSUser
from msgraph.generated.models.user_collection_response import UserCollectionResponse
from msgraph.generated.models.verified_domain import VerifiedDomain
from rest_framework.test import APITestCase

from authentik.admin.models import SystemSettings
from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.enterprise.providers.microsoft_entra.models import (
    MicrosoftEntraProvider,
    MicrosoftEntraProviderMapping,
    MicrosoftEntraProviderUser,
)
from authentik.enterprise.providers.microsoft_entra.tasks import microsoft_entra_sync
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction
from authentik.tasks.models import Task, TaskStatus


class MicrosoftEntraUserTests(APITestCase):
    """Microsoft Entra User tests"""

    @apply_blueprint("system/providers-microsoft-entra.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        SystemSettings.objects.update(avatars="none")
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.provider: MicrosoftEntraProvider = MicrosoftEntraProvider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            tenant_id=generate_id(),
            exclude_users_service_account=True,
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.property_mappings.add(
            MicrosoftEntraProviderMapping.objects.get(
                managed="goauthentik.io/providers/microsoft_entra/user"
            )
        )
        self.provider.property_mappings_group.add(
            MicrosoftEntraProviderMapping.objects.get(
                managed="goauthentik.io/providers/microsoft_entra/group"
            )
        )
        self.creds = ClientSecretCredential(generate_id(), generate_id(), generate_id())

    def test_user_create(self):
        """Test user creation"""
        uid = generate_id()
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_create,
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            microsoft_user = MicrosoftEntraProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(microsoft_user)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_create.assert_called_once()

    def _graph_patches(self):
        """Patch Graph credentials and the organization lookup every client makes"""
        return (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
        )

    def _graph_error(self, status: int, message: str) -> ODataError:
        """Build the error Graph raises for an error response"""
        error = ODataError(error=MainError(code="Request_BadRequest", message=message))
        error.response_status_code = status
        return error

    def _assert_warning(self, user: User, *messages: str):
        log = Task.objects.get(
            _uid=f"{self.provider.name}:user:{user.pk}:direct",
        ).tasklogs.get(log_level=TaskStatus.WARNING)
        self.assertIn(f"Failed to sync {user}", log.event)
        for message in messages:
            self.assertIn(message, log.event)

    def test_user_create_conflict(self):
        """A user that already exists in Entra ID is linked"""
        uid = generate_id()
        remote_id = generate_id()
        credentials, organization = self._graph_patches()
        with (
            credentials,
            organization,
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(side_effect=self._graph_error(409, "Conflict")),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.get",
                AsyncMock(
                    return_value=UserCollectionResponse(
                        value=[MSUser(id=remote_id, mail=f"{uid}@goauthentik.io")]
                    )
                ),
            ),
        ):
            user = User.objects.create(username=uid, email=f"{uid}@goauthentik.io")
        microsoft_user = MicrosoftEntraProviderUser.objects.get(provider=self.provider, user=user)
        self.assertEqual(microsoft_user.microsoft_id, remote_id)
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())

    def test_user_create_conflict_unmatched(self):
        """A user that conflicts with an Entra ID user that can't be found is reported"""
        uid = generate_id()
        credentials, organization = self._graph_patches()
        with (
            credentials,
            organization,
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(side_effect=self._graph_error(409, "Conflict")),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.get",
                AsyncMock(return_value=UserCollectionResponse(value=[])),
            ),
        ):
            user = User.objects.create(username=uid, email=f"{uid}@goauthentik.io")
        self.assertFalse(
            MicrosoftEntraProviderUser.objects.filter(provider=self.provider, user=user).exists()
        )
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())
        self._assert_warning(user, "Delete or rename the conflicting object")

    def test_user_create_bad_request(self):
        """A user that Entra ID rejects is reported with Graph's error message"""
        uid = generate_id()
        message = (
            "Another object with the same value for property userPrincipalName already exists."
        )
        credentials, organization = self._graph_patches()
        with (
            credentials,
            organization,
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(side_effect=self._graph_error(400, message)),
            ),
        ):
            user = User.objects.create(username=uid, email=f"{uid}@goauthentik.io")
        self.assertFalse(
            MicrosoftEntraProviderUser.objects.filter(provider=self.provider, user=user).exists()
        )
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())
        self._assert_warning(user, f"Bad request: {message}")

    def test_user_update_not_found(self):
        """A user that was deleted in Entra ID is created again"""
        uid = generate_id()
        remote_id = generate_id()
        credentials, organization = self._graph_patches()
        with (
            credentials,
            organization,
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(return_value=MSUser(id=remote_id)),
            ) as user_create,
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.patch",
                AsyncMock(side_effect=self._graph_error(404, "Resource does not exist")),
            ),
        ):
            user = User.objects.create(username=uid, email=f"{uid}@goauthentik.io")
            MicrosoftEntraProviderUser.objects.filter(provider=self.provider, user=user).update(
                microsoft_id=generate_id()
            )
            user.name = "new name"
            user.save()
        microsoft_user = MicrosoftEntraProviderUser.objects.get(provider=self.provider, user=user)
        self.assertEqual(microsoft_user.microsoft_id, remote_id)
        self.assertEqual(user_create.call_count, 2)
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())

    def test_user_create_dry_run(self):
        """Test user creation (dry run)"""
        self.provider.dry_run = True
        self.provider.save()
        uid = generate_id()
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            microsoft_user = MicrosoftEntraProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNone(microsoft_user)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())

    def test_user_not_created(self):
        """Test without property mappings, no group is created"""
        self.provider.property_mappings.clear()
        uid = generate_id()
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_create,
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            microsoft_user = MicrosoftEntraProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNone(microsoft_user)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_create.assert_not_called()

    def test_user_create_update(self):
        """Test user updating"""
        uid = generate_id()
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_create,
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.patch",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_patch,
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            microsoft_user = MicrosoftEntraProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(microsoft_user)

            user.name = "new name"
            user.save()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_create.assert_called_once()
            user_patch.assert_called_once()

    def test_user_create_delete(self):
        """Test user deletion"""
        uid = generate_id()
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_create,
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.delete",
                AsyncMock(),
            ) as user_delete,
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            microsoft_user = MicrosoftEntraProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(microsoft_user)

            user.delete()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_create.assert_called_once()
            user_delete.assert_called_once()

    def test_user_create_delete_suspend(self):
        """Test user deletion (delete action = Suspend)"""
        self.provider.user_delete_action = OutgoingSyncDeleteAction.SUSPEND
        self.provider.save()
        uid = generate_id()
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_create,
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.patch",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_patch,
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.delete",
                AsyncMock(),
            ) as user_delete,
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            microsoft_user = MicrosoftEntraProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(microsoft_user)

            user.delete()
            self.assertFalse(
                MicrosoftEntraProviderUser.objects.filter(
                    provider=self.provider, user__username=uid
                ).exists()
            )
            user_create.assert_called_once()
            user_patch.assert_called_once()
            self.assertFalse(user_patch.call_args[0][0].account_enabled)
            user_delete.assert_not_called()

    def test_user_create_delete_do_nothing(self):
        """Test user deletion (delete action = do nothing)"""
        self.provider.user_delete_action = OutgoingSyncDeleteAction.DO_NOTHING
        self.provider.save()
        uid = generate_id()
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.post",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_create,
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.patch",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ) as user_patch,
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.delete",
                AsyncMock(),
            ) as user_delete,
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            microsoft_user = MicrosoftEntraProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(microsoft_user)

            user.delete()
            self.assertFalse(
                MicrosoftEntraProviderUser.objects.filter(
                    provider=self.provider, user__username=uid
                ).exists()
            )
            user_create.assert_called_once()
            user_patch.assert_not_called()
            user_delete.assert_not_called()

    def test_sync_discover(self):
        """Test user discovery"""
        uid = generate_id()
        self.app.backchannel_providers.remove(self.provider)
        different_user = User.objects.create(
            username=uid,
            email=f"{uid}@goauthentik.io",
        )
        self.app.backchannel_providers.add(self.provider)
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.patch",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.get",
                AsyncMock(
                    return_value=UserCollectionResponse(
                        value=[MSUser(mail=f"{uid}@goauthentik.io", id=uid)]
                    )
                ),
            ) as user_list,
            patch(
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.get",
                AsyncMock(return_value=GroupCollectionResponse(value=[])),
            ),
        ):
            microsoft_entra_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                MicrosoftEntraProviderUser.objects.filter(
                    user=different_user, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_list.assert_called_once()

    def test_sync_discover_multiple(self):
        """Test user discovery (multiple times)"""
        uid = generate_id()
        self.app.backchannel_providers.remove(self.provider)
        different_user = User.objects.create(
            username=uid,
            email=f"{uid}@goauthentik.io",
        )
        self.app.backchannel_providers.add(self.provider)
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "msgraph.generated.users.item.user_item_request_builder.UserItemRequestBuilder.patch",
                AsyncMock(return_value=MSUser(id=generate_id())),
            ),
            patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.get",
                AsyncMock(
                    return_value=UserCollectionResponse(
                        value=[MSUser(mail=f"{uid}@goauthentik.io", id=uid)]
                    )
                ),
            ) as user_list,
            patch(
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.get",
                AsyncMock(return_value=GroupCollectionResponse(value=[])),
            ),
        ):
            microsoft_entra_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                MicrosoftEntraProviderUser.objects.filter(
                    user=different_user, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_list.assert_called_once()

            with patch(
                "msgraph.generated.users.users_request_builder.UsersRequestBuilder.get",
                AsyncMock(
                    return_value=UserCollectionResponse(
                        value=[MSUser(mail=f"{uid}@goauthentik.io", id=uid, about_me="foo")]
                    )
                ),
            ) as mod_user_list:
                microsoft_entra_sync.send(self.provider.pk).get_result()
                self.assertTrue(
                    MicrosoftEntraProviderUser.objects.filter(
                        user=different_user, provider=self.provider
                    ).exists()
                )
                self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
                mod_user_list.assert_called_once()

    def test_connect_manual(self):
        """test manual user connection"""
        uid = generate_id()
        self.app.backchannel_providers.remove(self.provider)
        admin = create_test_admin_user()
        different_user = User.objects.create(
            username=uid,
            email=f"{uid}@goauthentik.io",
        )
        self.app.backchannel_providers.add(self.provider)
        with (
            patch(
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.organization.organization_request_builder.OrganizationRequestBuilder.get",
                AsyncMock(
                    return_value=OrganizationCollectionResponse(
                        value=[
                            Organization(verified_domains=[VerifiedDomain(name="goauthentik.io")])
                        ]
                    )
                ),
            ),
            patch(
                "authentik.enterprise.providers.microsoft_entra.clients.users.MicrosoftEntraUserClient.update_single_attribute",
                MagicMock(),
            ) as user_get,
        ):
            self.client.force_login(admin)
            response = self.client.post(
                reverse("authentik_api:microsoftentraprovideruser-list"),
                data={
                    "microsoft_id": generate_id(),
                    "user": different_user.pk,
                    "provider": self.provider.pk,
                },
            )
            self.assertEqual(response.status_code, 201)
            user_get.assert_called_once()
