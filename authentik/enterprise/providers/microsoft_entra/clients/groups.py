from deepmerge import always_merger
from django.db import transaction
from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder
from msgraph.generated.models.group import Group as MSGroup
from msgraph.generated.models.reference_create import ReferenceCreate

from authentik.core.models import Group
from authentik.enterprise.providers.microsoft_entra.clients.base import MicrosoftEntraSyncClient
from authentik.enterprise.providers.microsoft_entra.models import (
    MicrosoftEntraProvider,
    MicrosoftEntraProviderGroup,
    MicrosoftEntraProviderMapping,
    MicrosoftEntraProviderUser,
)
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsSyncException,
    StopSync,
    TransientSyncException,
)
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction


class MicrosoftEntraGroupClient(
    MicrosoftEntraSyncClient[Group, MicrosoftEntraProviderGroup, MSGroup]
):
    """Microsoft client for groups"""

    connection_type = MicrosoftEntraProviderGroup
    connection_type_query = "group"
    can_discover = True

    def __init__(self, provider: MicrosoftEntraProvider) -> None:
        super().__init__(provider)
        self.mapper = PropertyMappingManager(
            self.provider.property_mappings_group.all().order_by("name").select_subclasses(),
            MicrosoftEntraProviderMapping,
            ["group", "provider", "connection"],
        )

    def to_schema(self, obj: Group, connection: MicrosoftEntraProviderGroup) -> MSGroup:
        """Convert authentik group"""
        raw_microsoft_group = super().to_schema(obj, connection)
        try:
            return MSGroup(**raw_microsoft_group)
        except TypeError as exc:
            raise StopSync(exc, obj) from exc

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
        microsoft_group = self.to_schema(group, None)
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
                if group_data.odata_count < 1 or len(group_data.value) < 1:
                    self.logger.warning(
                        "Group which could not be created also does not exist", group=group
                    )
                    return
                ms_group = group_data.value[0]
                return MicrosoftEntraProviderGroup.objects.create(
                    provider=self.provider,
                    group=group,
                    microsoft_id=ms_group.id,
                    attributes=self.entity_as_dict(ms_group),
                )
            else:
                return MicrosoftEntraProviderGroup.objects.create(
                    provider=self.provider,
                    group=group,
                    microsoft_id=response.id,
                    attributes=self.entity_as_dict(response),
                )

    def update(self, group: Group, connection: MicrosoftEntraProviderGroup):
        """Update existing group"""
        microsoft_group = self.to_schema(group, connection)
        microsoft_group.id = connection.microsoft_id
        try:
            response = self._request(
                self.client.groups.by_group_id(connection.microsoft_id).patch(microsoft_group)
            )
            if response:
                always_merger.merge(connection.attributes, self.entity_as_dict(response))
                connection.save()
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise

    def write(self, obj: Group):
        microsoft_group, created = super().write(obj)
        self.create_sync_members(obj, microsoft_group)
        return microsoft_group, created

    def create_sync_members(self, obj: Group, microsoft_group: MicrosoftEntraProviderGroup):
        """Sync all members after a group was created"""
        users = list(obj.users.order_by("id").values_list("id", flat=True))
        connections = MicrosoftEntraProviderUser.objects.filter(
            provider=self.provider, user__pk__in=users
        ).values_list("microsoft_id", flat=True)
        self._patch(microsoft_group.microsoft_id, Direction.add, connections)

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
                        .members.by_directory_object_id(user)
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
            attributes=self.entity_as_dict(group),
        )

    def update_single_attribute(self, connection: MicrosoftEntraProviderGroup):
        data = self._request(self.client.groups.by_group_id(connection.microsoft_id).get())
        connection.attributes = self.entity_as_dict(data)
