from deepmerge import always_merger
from django.db import transaction

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import Group
from authentik.enterprise.providers.google.clients.base import GoogleSyncClient
from authentik.enterprise.providers.google.models import (
    GoogleProviderGroup,
    GoogleProviderMapping,
    GoogleProviderUser,
)
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsException,
    StopSync,
    TransientSyncException,
)
from authentik.lib.utils.errors import exception_to_string


class GoogleGroupClient(GoogleSyncClient[Group, dict]):
    """Google client for groups"""

    def delete(self, obj: Group):
        """Delete group"""
        google_group = GoogleProviderGroup.objects.filter(provider=self.provider, group=obj).first()
        if not google_group:
            self.logger.debug("Group does not exist in Google, skipping")
            return None
        with transaction.atomic():
            response = self._request(
                self.directory_service.groups().delete(groupKey=google_group.id)
            )
            google_group.delete()
            return response

    def to_schema(self, obj: Group) -> dict:
        """Convert authentik group"""
        raw_google_group = {}
        for mapping in (
            self.provider.property_mappings_group.all().order_by("name").select_subclasses()
        ):
            if not isinstance(mapping, GoogleProviderMapping):
                continue
            try:
                mapping: GoogleProviderMapping
                value = mapping.evaluate(
                    user=None,
                    request=None,
                    group=obj,
                    provider=self.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_google_group, value)
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

    def _create(self, group: Group):
        """Create group from scratch and create a connection object"""
        google_group = self.to_schema(group)
        with transaction.atomic():
            response = self._request(self.directory_service.groups().insert(body=google_group))
            GoogleProviderGroup.objects.create(
                provider=self.provider, group=group, id=response["id"]
            )

    def _update(self, group: Group, connection: GoogleProviderGroup):
        """Update existing group"""
        google_group = self.to_schema(group)
        try:
            return self._request(
                self.directory_service.groups().update(
                    groupKey=connection.id,
                    body=google_group,
                )
            )
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise

    def _write(self, obj: Group):
        """Write a group"""
        google_group = GoogleProviderGroup.objects.filter(provider=self.provider, group=obj).first()
        if not google_group:
            return self._create(obj), True
        try:
            return self._update(obj, google_group), False
        except NotFoundSyncException:
            google_group.delete()
            return self._create(obj), True

    def write(self, obj: Group):
        google_group, created = self._write(obj)
        if created:
            self.create_sync_members(obj, google_group)
        return google_group

    def create_sync_members(self, obj: Group, google_group: dict):
        """Sync all members after a group was created"""
        users = list(obj.users.order_by("id").values_list("id", flat=True))
        connections = GoogleProviderUser.objects.filter(provider=self.provider, user__pk__in=users)
        for user in connections:
            try:
                self._request(
                    self.directory_service.members().insert(
                        groupKey=google_group["id"],
                        body={
                            "email": user.id,
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
            except ObjectExistsException:
                pass
            except TransientSyncException:
                raise

    def _patch_add_users(self, group: Group, users_set: set[int]):
        """Add users in users_set to group"""
        if len(users_set) < 1:
            return
        google_group = GoogleProviderGroup.objects.filter(
            provider=self.provider, group=group
        ).first()
        if not google_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            GoogleProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(google_group.id, Direction.add, user_ids)

    def _patch_remove_users(self, group: Group, users_set: set[int]):
        """Remove users in users_set from group"""
        if len(users_set) < 1:
            return
        google_group = GoogleProviderGroup.objects.filter(
            provider=self.provider, group=group
        ).first()
        if not google_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            GoogleProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(google_group.id, Direction.remove, user_ids)
