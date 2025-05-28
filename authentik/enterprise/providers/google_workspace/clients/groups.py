from django.db import transaction
from django.utils.text import slugify

from authentik.core.models import Group
from authentik.enterprise.providers.google_workspace.clients.base import GoogleWorkspaceSyncClient
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceProvider,
    GoogleWorkspaceProviderGroup,
    GoogleWorkspaceProviderMapping,
    GoogleWorkspaceProviderUser,
)
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsSyncException,
    TransientSyncException,
)
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction


class GoogleWorkspaceGroupClient(
    GoogleWorkspaceSyncClient[Group, GoogleWorkspaceProviderGroup, dict]
):
    """Google client for groups"""

    connection_type = GoogleWorkspaceProviderGroup
    connection_attr = "googleworkspaceprovidergroup_set"
    can_discover = True

    def __init__(self, provider: GoogleWorkspaceProvider) -> None:
        super().__init__(provider)
        self.mapper = PropertyMappingManager(
            self.provider.property_mappings_group.all().order_by("name").select_subclasses(),
            GoogleWorkspaceProviderMapping,
            ["group", "provider", "connection"],
        )

    def to_schema(self, obj: Group, connection: GoogleWorkspaceProviderGroup) -> dict:
        """Convert authentik group"""
        return super().to_schema(
            obj,
            connection=connection,
            email=f"{slugify(obj.name)}@{self.provider.default_group_email_domain}",
        )

    def delete(self, obj: Group):
        """Delete group"""
        google_group = GoogleWorkspaceProviderGroup.objects.filter(
            provider=self.provider, group=obj
        ).first()
        if not google_group:
            self.logger.debug("Group does not exist in Google, skipping")
            return None
        with transaction.atomic():
            if self.provider.group_delete_action == OutgoingSyncDeleteAction.DELETE:
                self._request(
                    self.directory_service.groups().delete(groupKey=google_group.google_id)
                )
            google_group.delete()

    def create(self, group: Group):
        """Create group from scratch and create a connection object"""
        google_group = self.to_schema(group, None)
        self.check_email_valid(google_group["email"])
        with transaction.atomic():
            try:
                response = self._request(self.directory_service.groups().insert(body=google_group))
            except ObjectExistsSyncException:
                # group already exists in google workspace, so we can connect them manually
                # for groups we need to fetch the group from google as we connect on
                # ID and not group email
                group_data = self._request(
                    self.directory_service.groups().get(groupKey=google_group["email"])
                )
                return GoogleWorkspaceProviderGroup.objects.create(
                    provider=self.provider,
                    group=group,
                    google_id=group_data["id"],
                    attributes=group_data,
                )
            else:
                return GoogleWorkspaceProviderGroup.objects.create(
                    provider=self.provider,
                    group=group,
                    google_id=response["id"],
                    attributes=response,
                )

    def update(self, group: Group, connection: GoogleWorkspaceProviderGroup):
        """Update existing group"""
        google_group = self.to_schema(group, connection)
        self.check_email_valid(google_group["email"])
        try:
            response = self._request(
                self.directory_service.groups().update(
                    groupKey=connection.google_id,
                    body=google_group,
                )
            )
            connection.attributes = response
            connection.save()
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise

    def write(self, obj: Group):
        google_group, created = super().write(obj)
        self.create_sync_members(obj, google_group)
        return google_group, created

    def create_sync_members(self, obj: Group, google_group: GoogleWorkspaceProviderGroup):
        """Sync all members after a group was created"""
        users = list(obj.users.order_by("id").values_list("id", flat=True))
        connections = GoogleWorkspaceProviderUser.objects.filter(
            provider=self.provider, user__pk__in=users
        ).values_list("google_id", flat=True)
        self._patch(google_group.google_id, Direction.add, connections)

    def update_group(self, group: Group, action: Direction, users_set: set[int]):
        """Update a groups members"""
        if action == Direction.add:
            return self._patch_add_users(group, users_set)
        if action == Direction.remove:
            return self._patch_remove_users(group, users_set)

    def _patch(self, google_group_id: str, direction: Direction, members: list[str]):
        for user in members:
            try:
                if direction == Direction.add:
                    self._request(
                        self.directory_service.members().insert(
                            groupKey=google_group_id, body={"email": user}
                        )
                    )
                if direction == Direction.remove:
                    self._request(
                        self.directory_service.members().delete(
                            groupKey=google_group_id, memberKey=user
                        )
                    )
            except ObjectExistsSyncException:
                pass
            except TransientSyncException:
                raise

    def _patch_add_users(self, group: Group, users_set: set[int]):
        """Add users in users_set to group"""
        if len(users_set) < 1:
            return
        google_group = GoogleWorkspaceProviderGroup.objects.filter(
            provider=self.provider, group=group
        ).first()
        if not google_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            GoogleWorkspaceProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("google_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(google_group.google_id, Direction.add, user_ids)

    def _patch_remove_users(self, group: Group, users_set: set[int]):
        """Remove users in users_set from group"""
        if len(users_set) < 1:
            return
        google_group = GoogleWorkspaceProviderGroup.objects.filter(
            provider=self.provider, group=group
        ).first()
        if not google_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            GoogleWorkspaceProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("google_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(google_group.google_id, Direction.remove, user_ids)

    def discover(self):
        """Iterate through all groups and connect them with authentik groups if possible"""
        request = self.directory_service.groups().list(
            customer="my_customer", maxResults=500, orderBy="email"
        )
        while request:
            response = request.execute()
            for group in response.get("groups", []):
                self._discover_single_group(group)
            request = self.directory_service.groups().list_next(
                previous_request=request, previous_response=response
            )

    def _discover_single_group(self, group: dict):
        """handle discovery of a single group"""
        google_name = group["name"]
        google_id = group["id"]
        matching_authentik_group = (
            self.provider.get_object_qs(Group).filter(name=google_name).first()
        )
        if not matching_authentik_group:
            return
        GoogleWorkspaceProviderGroup.objects.get_or_create(
            provider=self.provider,
            group=matching_authentik_group,
            google_id=google_id,
            attributes=group,
        )

    def update_single_attribute(self, connection: GoogleWorkspaceProviderUser):
        group = self.directory_service.groups().get(connection.google_id)
        connection.attributes = group
