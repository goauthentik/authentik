from deepmerge import always_merger
from django.db import transaction
from django.utils.text import slugify

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
    SkipObjectException,
)
from authentik.core.models import Group
from authentik.enterprise.providers.google_workspace.clients.base import GoogleWorkspaceSyncClient
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceDeleteAction,
    GoogleWorkspaceProviderGroup,
    GoogleWorkspaceProviderMapping,
    GoogleWorkspaceProviderUser,
)
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsSyncException,
    StopSync,
    TransientSyncException,
)
from authentik.lib.utils.errors import exception_to_string


class GoogleWorkspaceGroupClient(
    GoogleWorkspaceSyncClient[Group, GoogleWorkspaceProviderGroup, dict]
):
    """Google client for groups"""

    connection_type = GoogleWorkspaceProviderGroup
    connection_type_query = "group"
    can_discover = True

    def to_schema(self, obj: Group) -> dict:
        """Convert authentik group"""
        raw_google_group = {
            "email": f"{slugify(obj.name)}@{self.provider.default_group_email_domain}"
        }
        for mapping in (
            self.provider.property_mappings_group.all().order_by("name").select_subclasses()
        ):
            if not isinstance(mapping, GoogleWorkspaceProviderMapping):
                continue
            try:
                mapping: GoogleWorkspaceProviderMapping
                value = mapping.evaluate(
                    user=None,
                    request=None,
                    group=obj,
                    provider=self.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_google_group, value)
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
        if not raw_google_group:
            raise StopSync(ValueError("No group mappings configured"), obj)

        return raw_google_group

    def delete(self, obj: Group):
        """Delete group"""
        google_group = GoogleWorkspaceProviderGroup.objects.filter(
            provider=self.provider, group=obj
        ).first()
        if not google_group:
            self.logger.debug("Group does not exist in Google, skipping")
            return None
        with transaction.atomic():
            if self.provider.group_delete_action == GoogleWorkspaceDeleteAction.DELETE:
                self._request(
                    self.directory_service.groups().delete(groupKey=google_group.google_id)
                )
            google_group.delete()

    def create(self, group: Group):
        """Create group from scratch and create a connection object"""
        google_group = self.to_schema(group)
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
                GoogleWorkspaceProviderGroup.objects.create(
                    provider=self.provider, group=group, google_id=group_data["id"]
                )
            else:
                GoogleWorkspaceProviderGroup.objects.create(
                    provider=self.provider, group=group, google_id=response["id"]
                )

    def update(self, group: Group, connection: GoogleWorkspaceProviderGroup):
        """Update existing group"""
        google_group = self.to_schema(group)
        self.check_email_valid(google_group["email"])
        try:
            return self._request(
                self.directory_service.groups().update(
                    groupKey=connection.google_id,
                    body=google_group,
                )
            )
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise

    def write(self, obj: Group):
        google_group, created = super().write(obj)
        if created:
            self.create_sync_members(obj, google_group)
        return google_group

    def create_sync_members(self, obj: Group, google_group: dict):
        """Sync all members after a group was created"""
        users = list(obj.users.order_by("id").values_list("id", flat=True))
        connections = GoogleWorkspaceProviderUser.objects.filter(
            provider=self.provider, user__pk__in=users
        )
        for user in connections:
            try:
                self._request(
                    self.directory_service.members().insert(
                        groupKey=google_group["id"],
                        body={
                            "email": user.google_id,
                        },
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
        )
