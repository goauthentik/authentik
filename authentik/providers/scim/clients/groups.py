"""Group client"""

from itertools import batched

from django.db import transaction
from pydantic import ValidationError
from pydanticscim.group import GroupMember
from pydanticscim.responses import PatchOp

from authentik.core.models import Group
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsSyncException,
    StopSync,
)
from authentik.policies.utils import delete_none_values
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import (
    SCIMRequestException,
)
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA, PatchOperation, PatchRequest
from authentik.providers.scim.clients.schema import Group as SCIMGroupSchema
from authentik.providers.scim.models import (
    SCIMMapping,
    SCIMProvider,
    SCIMProviderGroup,
    SCIMProviderUser,
)


class SCIMGroupClient(SCIMClient[Group, SCIMProviderGroup, SCIMGroupSchema]):
    """SCIM client for groups"""

    connection_type = SCIMProviderGroup
    connection_attr = "scimprovidergroup_set"
    mapper: PropertyMappingManager

    def __init__(self, provider: SCIMProvider):
        super().__init__(provider)
        self.mapper = PropertyMappingManager(
            self.provider.property_mappings_group.all().order_by("name").select_subclasses(),
            SCIMMapping,
            ["group", "provider", "connection"],
        )

    def to_schema(self, obj: Group, connection: SCIMProviderGroup) -> SCIMGroupSchema:
        """Convert authentik user into SCIM"""
        raw_scim_group = super().to_schema(
            obj,
            connection,
            schemas=(SCIM_GROUP_SCHEMA,),
        )
        try:
            scim_group = SCIMGroupSchema.model_validate(delete_none_values(raw_scim_group))
        except ValidationError as exc:
            raise StopSync(exc, obj) from exc
        if not scim_group.externalId:
            scim_group.externalId = str(obj.pk)

        if not self._config.patch.supported:
            users = list(obj.users.order_by("id").values_list("id", flat=True))
            connections = SCIMProviderUser.objects.filter(
                provider=self.provider, user__pk__in=users
            )
            members = []
            for user in connections:
                members.append(
                    GroupMember(
                        value=user.scim_id,
                    )
                )
            if members:
                scim_group.members = members
        else:
            del scim_group.members
        return scim_group

    def delete(self, obj: Group):
        """Delete group"""
        scim_group = SCIMProviderGroup.objects.filter(provider=self.provider, group=obj).first()
        if not scim_group:
            self.logger.debug("Group does not exist in SCIM, skipping")
            return None
        response = self._request("DELETE", f"/Groups/{scim_group.scim_id}")
        scim_group.delete()
        return response

    def create(self, group: Group):
        """Create group from scratch and create a connection object"""
        scim_group = self.to_schema(group, None)
        response = self._request(
            "POST",
            "/Groups",
            json=scim_group.model_dump(
                mode="json",
                exclude_unset=True,
            ),
        )
        scim_id = response.get("id")
        if not scim_id or scim_id == "":
            raise StopSync("SCIM Response with missing or invalid `id`")
        connection = SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id=scim_id, attributes=response
        )
        users = list(group.users.order_by("id").values_list("id", flat=True))
        self._patch_add_users(connection, users)
        return connection

    def update(self, group: Group, connection: SCIMProviderGroup):
        """Update existing group"""
        scim_group = self.to_schema(group, connection)
        scim_group.id = connection.scim_id
        try:
            if self._config.patch.supported:
                return self._update_patch(group, scim_group, connection)
            return self._update_put(group, scim_group, connection)
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise

    def _update_patch(
        self, group: Group, scim_group: SCIMGroupSchema, connection: SCIMProviderGroup
    ):
        """Update a group via PATCH request"""
        # Patch group's attributes instead of replacing it and re-adding users if we can
        self._request(
            "PATCH",
            f"/Groups/{connection.scim_id}",
            json=PatchRequest(
                Operations=[
                    PatchOperation(
                        op=PatchOp.replace,
                        path=None,
                        value=scim_group.model_dump(mode="json", exclude_unset=True),
                    )
                ]
            ).model_dump(
                mode="json",
                exclude_unset=True,
                exclude_none=True,
            ),
        )
        return self.patch_compare_users(group)

    def _update_put(self, group: Group, scim_group: SCIMGroupSchema, connection: SCIMProviderGroup):
        """Update a group via PUT request"""
        try:
            self._request(
                "PUT",
                f"/Groups/{connection.scim_id}",
                json=scim_group.model_dump(
                    mode="json",
                    exclude_unset=True,
                ),
            )
            return self.patch_compare_users(group)
        except (SCIMRequestException, ObjectExistsSyncException):
            # Some providers don't support PUT on groups, so this is mainly a fix for the initial
            # sync, send patch add requests for all the users the group currently has
            return self._update_patch(group, scim_group, connection)

    def update_group(self, group: Group, action: Direction, users_set: set[int]):
        """Update a group, either using PUT to replace it or PATCH if supported"""
        scim_group = SCIMProviderGroup.objects.filter(provider=self.provider, group=group).first()
        if not scim_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        if self._config.patch.supported:
            if action == Direction.add:
                return self._patch_add_users(scim_group, users_set)
            if action == Direction.remove:
                return self._patch_remove_users(scim_group, users_set)
        try:
            return self.write(group)
        except SCIMRequestException as exc:
            if self._config.is_fallback:
                # Assume that provider does not support PUT and also doesn't support
                # ServiceProviderConfig, so try PATCH as a fallback
                if action == Direction.add:
                    return self._patch_add_users(scim_group, users_set)
                if action == Direction.remove:
                    return self._patch_remove_users(scim_group, users_set)
            raise exc

    def _patch_chunked(
        self,
        group_id: str,
        *ops: PatchOperation,
    ):
        """Helper function that chunks patch requests based on the maxOperations attribute.
        This is not strictly according to specs but there's nothing in the schema that allows the
        us to know what the maximum patch operations per request should be."""
        chunk_size = self._config.bulk.maxOperations
        if chunk_size < 1:
            chunk_size = len(ops)
        if len(ops) < 1:
            return
        for chunk in batched(ops, chunk_size, strict=False):
            req = PatchRequest(Operations=list(chunk))
            self._request(
                "PATCH",
                f"/Groups/{group_id}",
                json=req.model_dump(
                    mode="json",
                ),
            )

    @transaction.atomic
    def patch_compare_users(self, group: Group):
        """Compare users with a SCIM group and add/remove any differences"""
        # Get scim group first
        scim_group = SCIMProviderGroup.objects.filter(provider=self.provider, group=group).first()
        if not scim_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        # Get a list of all users in the authentik group
        raw_users_should = list(group.users.order_by("id").values_list("id", flat=True))
        # Lookup the SCIM IDs of the users
        users_should: list[str] = list(
            SCIMProviderUser.objects.filter(
                user__pk__in=raw_users_should, provider=self.provider
            ).values_list("scim_id", flat=True)
        )
        if len(raw_users_should) != len(users_should):
            self.logger.warning(
                "User count mismatch, not all users in the group are synced to SCIM yet.",
                group=group,
            )
        # Get current group status
        current_group = SCIMGroupSchema.model_validate(
            self._request("GET", f"/Groups/{scim_group.scim_id}")
        )
        users_to_add = []
        users_to_remove = []
        # Check users currently in group and if they shouldn't be in the group and remove them
        for user in current_group.members or []:
            if user.value not in users_should:
                users_to_remove.append(user.value)
        # Check users that should be in the group and add them
        if current_group.members is not None:
            for user in users_should:
                if len([x for x in current_group.members if x.value == user]) < 1:
                    users_to_add.append(user)
        # Only send request if we need to make changes
        if len(users_to_add) < 1 and len(users_to_remove) < 1:
            return
        return self._patch_chunked(
            scim_group.scim_id,
            *[
                PatchOperation(
                    op=PatchOp.add,
                    path="members",
                    value=[{"value": x}],
                )
                for x in users_to_add
            ],
            *[
                PatchOperation(
                    op=PatchOp.remove,
                    path="members",
                    value=[{"value": x}],
                )
                for x in users_to_remove
            ],
        )

    def _patch_add_users(self, scim_group: SCIMProviderGroup, users_set: set[int]):
        """Add users in users_set to group"""
        if len(users_set) < 1:
            return
        user_ids = list(
            SCIMProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("scim_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch_chunked(
            scim_group.scim_id,
            *[
                PatchOperation(
                    op=PatchOp.add,
                    path="members",
                    value=[{"value": x}],
                )
                for x in user_ids
            ],
        )

    def _patch_remove_users(self, scim_group: SCIMProviderGroup, users_set: set[int]):
        """Remove users in users_set from group"""
        if len(users_set) < 1:
            return
        user_ids = list(
            SCIMProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("scim_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch_chunked(
            scim_group.scim_id,
            *[
                PatchOperation(
                    op=PatchOp.remove,
                    path="members",
                    value=[{"value": x}],
                )
                for x in user_ids
            ],
        )
