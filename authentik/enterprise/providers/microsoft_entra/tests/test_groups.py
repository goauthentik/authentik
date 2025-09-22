"""Microsoft Entra Group tests"""

from unittest.mock import AsyncMock, MagicMock, patch

from azure.identity.aio import ClientSecretCredential
from django.test import TestCase
from msgraph.generated.models.group import Group as MSGroup
from msgraph.generated.models.group_collection_response import GroupCollectionResponse
from msgraph.generated.models.organization import Organization
from msgraph.generated.models.organization_collection_response import OrganizationCollectionResponse
from msgraph.generated.models.user import User as MSUser
from msgraph.generated.models.user_collection_response import UserCollectionResponse
from msgraph.generated.models.verified_domain import VerifiedDomain

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.providers.microsoft_entra.models import (
    MicrosoftEntraProvider,
    MicrosoftEntraProviderGroup,
    MicrosoftEntraProviderMapping,
    MicrosoftEntraProviderUser,
)
from authentik.enterprise.providers.microsoft_entra.tasks import microsoft_entra_sync
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction
from authentik.tenants.models import Tenant


class MicrosoftEntraGroupTests(TestCase):
    """Microsoft Entra Group tests"""

    @apply_blueprint("system/providers-microsoft-entra.yaml")
    def setUp(self) -> None:
        # Delete all groups and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple groups
        Tenant.objects.update(avatars="none")
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

    def test_group_create(self):
        """Test group creation"""
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
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=generate_id())),
            ) as group_create,
        ):
            group = Group.objects.create(name=uid)
            microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(microsoft_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            group_create.assert_called_once()

    def test_group_not_created(self):
        """Test without group property mappings, no group is created"""
        self.provider.property_mappings_group.clear()
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
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=generate_id())),
            ) as group_create,
        ):
            group = Group.objects.create(name=uid)
            microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNone(microsoft_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            group_create.assert_not_called()

    def test_group_create_update(self):
        """Test group updating"""
        uid = generate_id()
        ext_id = generate_id()
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
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=ext_id)),
            ) as group_create,
            patch(
                "msgraph.generated.groups.item.group_item_request_builder.GroupItemRequestBuilder.patch",
                AsyncMock(return_value=MSGroup(id=ext_id)),
            ) as group_patch,
        ):
            group = Group.objects.create(name=uid)
            microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(microsoft_group)

            group.name = "new name"
            group.save()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            group_create.assert_called_once()
            group_patch.assert_called_once()

    def test_group_create_delete(self):
        """Test group deletion"""
        uid = generate_id()
        ext_id = generate_id()
        with (
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
                "authentik.enterprise.providers.microsoft_entra.models.MicrosoftEntraProvider.microsoft_credentials",
                MagicMock(return_value={"credentials": self.creds}),
            ),
            patch(
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=ext_id)),
            ) as group_create,
            patch(
                "msgraph.generated.groups.item.group_item_request_builder.GroupItemRequestBuilder.delete",
                AsyncMock(return_value=MSGroup(id=ext_id)),
            ) as group_delete,
        ):
            group = Group.objects.create(name=uid)
            microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(microsoft_group)

            group.delete()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            group_create.assert_called_once()
            group_delete.assert_called_once()

    def test_group_create_member_add(self):
        """Test group creation"""
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
            ),
            patch(
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=uid)),
            ) as group_create,
            patch(
                "msgraph.generated.groups.item.members.ref.ref_request_builder.RefRequestBuilder.post",
                AsyncMock(),
            ) as member_add,
        ):
            user = create_test_user(uid)
            group = Group.objects.create(name=uid)
            group.users.add(user)
            microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(microsoft_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_create.assert_called_once()
            group_create.assert_called_once()
            member_add.assert_called_once()
            self.assertEqual(
                member_add.call_args[0][0].odata_id,
                f"https://graph.microsoft.com/v1.0/directoryObjects/{
                    MicrosoftEntraProviderUser.objects.filter(
                        provider=self.provider,
                    )
                    .first()
                    .microsoft_id
                }",
            )

    def test_group_create_member_remove(self):
        """Test group creation"""
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
            ),
            patch(
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=uid)),
            ) as group_create,
            patch(
                "msgraph.generated.groups.item.members.ref.ref_request_builder.RefRequestBuilder.post",
                AsyncMock(),
            ) as member_add,
            patch(
                "msgraph.generated.groups.item.members.item.ref.ref_request_builder.RefRequestBuilder.delete",
                AsyncMock(),
            ) as member_remove,
        ):
            user = create_test_user(uid)
            group = Group.objects.create(name=uid)
            group.users.add(user)
            microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(microsoft_group)
            group.users.remove(user)

            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_create.assert_called_once()
            group_create.assert_called_once()
            member_add.assert_called_once()
            self.assertEqual(
                member_add.call_args[0][0].odata_id,
                f"https://graph.microsoft.com/v1.0/directoryObjects/{
                    MicrosoftEntraProviderUser.objects.filter(
                        provider=self.provider,
                    )
                    .first()
                    .microsoft_id
                }",
            )
            member_remove.assert_called_once()

    def test_group_create_delete_do_nothing(self):
        """Test group deletion (delete action = do nothing)"""
        self.provider.group_delete_action = OutgoingSyncDeleteAction.DO_NOTHING
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
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=uid)),
            ) as group_create,
            patch(
                "msgraph.generated.groups.item.group_item_request_builder.GroupItemRequestBuilder.delete",
                AsyncMock(return_value=MSGroup(id=uid)),
            ) as group_delete,
        ):
            group = Group.objects.create(name=uid)
            microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(microsoft_group)

            group.delete()
            self.assertFalse(
                MicrosoftEntraProviderGroup.objects.filter(
                    provider=self.provider, group__name=uid
                ).exists()
            )
            group_create.assert_called_once()
            group_delete.assert_not_called()

    def test_sync_task(self):
        """Test group discovery"""
        uid = generate_id()
        self.app.backchannel_providers.remove(self.provider)
        different_group = Group.objects.create(
            name=uid,
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
                "msgraph.generated.groups.groups_request_builder.GroupsRequestBuilder.post",
                AsyncMock(return_value=MSGroup(id=generate_id())),
            ),
            patch(
                "msgraph.generated.groups.item.group_item_request_builder.GroupItemRequestBuilder.patch",
                AsyncMock(return_value=MSGroup(id=uid)),
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
                AsyncMock(
                    return_value=GroupCollectionResponse(
                        value=[MSGroup(display_name=uid, unique_name=uid, id=uid)]
                    )
                ),
            ) as group_list,
        ):
            microsoft_entra_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                MicrosoftEntraProviderGroup.objects.filter(
                    group=different_group, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            user_list.assert_called_once()
            group_list.assert_called_once()
