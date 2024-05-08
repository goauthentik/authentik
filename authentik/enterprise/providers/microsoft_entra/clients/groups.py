from dacite import from_dict
from deepmerge import always_merger
from django.db import transaction
from msgraph.generated.models.group import Group as MSGroup
from msgraph.generated.models.reference_create import ReferenceCreate

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
    SkipObjectException,
)
from authentik.core.models import Group
from authentik.enterprise.providers.microsoft_entra.clients.base import MicrosoftEntraSyncClient
from authentik.enterprise.providers.microsoft_entra.models import (
    MicrosoftEntraProviderGroup,
    MicrosoftEntraProviderMapping,
    MicrosoftEntraProviderUser,
)
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsSyncException,
    StopSync,
    TransientSyncException,
)
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction
from authentik.lib.utils.errors import exception_to_string
from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder


class MicrosoftEntraGroupClient(
    MicrosoftEntraSyncClient[Group, MicrosoftEntraProviderGroup, MSGroup]
):
    """Microsoft client for groups"""

    connection_type = MicrosoftEntraProviderGroup
    connection_type_query = "group"
    can_discover = True

    def to_schema(self, obj: Group) -> MSGroup:
        """Convert authentik group"""
        raw_microsoft_group = {}
        for mapping in (
            self.provider.property_mappings_group.all().order_by("name").select_subclasses()
        ):
            if not isinstance(mapping, MicrosoftEntraProviderMapping):
                continue
            try:
                value = mapping.evaluate(
                    user=None,
                    request=None,
                    group=obj,
                    provider=self.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_microsoft_group, value)
            except SkipObjectException as exc:
                raise exc from exc
            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping {exception_to_string(exc)}",
                    mapping=mapping,
                ).save()
                raise StopSync(exc, obj, mapping) from exc
        if not raw_microsoft_group:
            raise StopSync(ValueError("No group mappings configured"), obj)

        return from_dict(MSGroup, raw_microsoft_group)

    def delete(self, obj: Group):
        """Delete group"""
        microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
            provider=self.provider, group=obj
        ).first()
        if not microsoft_group:
            self.logger.debug("Group does not exist in Microsoft, skipping")
            return None
        with transaction.atomic():
            if self.provider.group_delete_action == OutgoingSyncDeleteAction.DELETE:
                self._request(self.client.groups.by_group_id(microsoft_group.microsoft_id).delete())
            microsoft_group.delete()

    def create(self, group: Group):
        """Create group from scratch and create a connection object"""
        microsoft_group = self.to_schema(group)
        # self.check_email_valid(microsoft_group["email"])
        with transaction.atomic():
            try:
                response = self._request(self.client.groups.post(microsoft_group))
            except ObjectExistsSyncException:
                # group already exists in microsoft entra, so we can connect them manually
                # for groups we need to fetch the group from microsoft as we connect on
                # ID and not group email
                query_params = GroupsRequestBuilder.GroupsRequestBuilderGetQueryParameters(
                    filter=f"displayName eq '{microsoft_group.display_name}'",
                )
                request_configuration = (
                    GroupsRequestBuilder.GroupsRequestBuilderGetRequestConfiguration(
                        query_parameters=query_params,
                    )
                )
                group_data = self._request(self.client.groups.get(request_configuration))
                if group_data.odata_count < 1:
                    self.logger.warning(
                        "Group which could not be created also does not exist", group=group
                    )
                    return
                MicrosoftEntraProviderGroup.objects.create(
                    provider=self.provider, group=group, microsoft_id=group_data.value[0].id
                )
            else:
                MicrosoftEntraProviderGroup.objects.create(
                    provider=self.provider, group=group, microsoft_id=response.id
                )

    def update(self, group: Group, connection: MicrosoftEntraProviderGroup):
        """Update existing group"""
        microsoft_group = self.to_schema(group)
        # self.check_email_valid(microsoft_group["email"])
        try:
            return self._request(
                self.client.groups.by_group_id(connection.microsoft_id).update(microsoft_group)
            )
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise

    def write(self, obj: Group):
        microsoft_group, created = super().write(obj)
        if created:
            self.create_sync_members(obj, microsoft_group)
        return microsoft_group

    def create_sync_members(self, obj: Group, microsoft_group: MSGroup):
        """Sync all members after a group was created"""
        users = list(obj.users.order_by("id").values_list("id", flat=True))
        connections = MicrosoftEntraProviderUser.objects.filter(
            provider=self.provider, user__pk__in=users
        )
        for user in connections:
            try:
                request_body = ReferenceCreate(
                    odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{user.microsoft_id}",
                )
                self._request(
                    self.client.groups.by_group_id(microsoft_group.id).members.ref.post(
                        request_body
                    )
                )
            except TransientSyncException:
                continue

    def update_group(self, group: Group, action: Direction, users_set: set[int]):
        """Update a groups members"""
        if action == Direction.add:
            return self._patch_add_users(group, users_set)
        if action == Direction.remove:
            return self._patch_remove_users(group, users_set)

    def _patch(self, microsoft_group_id: str, direction: Direction, members: list[str]):
        for user in members:
            try:
                if direction == Direction.add:
                    request_body = ReferenceCreate(
                        odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{user}",
                    )
                    self._request(
                        self.client.groups.by_group_id(microsoft_group_id).members.ref.post(
                            request_body
                        )
                    )
                if direction == Direction.remove:
                    self._request(
                        self.client.groups.by_group_id(microsoft_group_id)
                        .by_directory_object_id(user)
                        .ref.delete()
                    )
            except ObjectExistsSyncException:
                pass
            except TransientSyncException:
                raise

    def _patch_add_users(self, group: Group, users_set: set[int]):
        """Add users in users_set to group"""
        if len(users_set) < 1:
            return
        microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
            provider=self.provider, group=group
        ).first()
        if not microsoft_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            MicrosoftEntraProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("microsoft_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(microsoft_group.microsoft_id, Direction.add, user_ids)

    def _patch_remove_users(self, group: Group, users_set: set[int]):
        """Remove users in users_set from group"""
        if len(users_set) < 1:
            return
        microsoft_group = MicrosoftEntraProviderGroup.objects.filter(
            provider=self.provider, group=group
        ).first()
        if not microsoft_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            MicrosoftEntraProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("microsoft_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(microsoft_group.microsoft_id, Direction.remove, user_ids)

    def discover(self):
        """Iterate through all groups and connect them with authentik groups if possible"""
        groups = self._request(self.client.groups.get())
        next_link = True
        while next_link:
            for group in groups.value:
                self._discover_single_group(group)
            next_link = groups.odata_next_link
            if not next_link:
                break
            groups = self._request(self.client.groups.with_url(next_link).get())

    def _discover_single_group(self, group: MSGroup):
        """handle discovery of a single group"""
        microsoft_name = group.unique_name
        matching_authentik_group = (
            self.provider.get_object_qs(Group).filter(name=microsoft_name).first()
        )
        if not matching_authentik_group:
            return
        MicrosoftEntraProviderGroup.objects.get_or_create(
            provider=self.provider,
            group=matching_authentik_group,
            microsoft_id=group.id,
        )
