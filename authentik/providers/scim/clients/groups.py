"""Group client"""

from itertools import batched

from pydantic import ValidationError
from pydanticscim.group import GroupMember
from pydanticscim.responses import PatchOp, PatchOperation

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
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA, PatchRequest
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
    connection_type_query = "group"
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
            provider=self.provider, group=group, scim_id=scim_id
        )
        users = list(group.users.order_by("id").values_list("id", flat=True))
        self._patch_add_users(group, users)
        return connection

    def update(self, group: Group, connection: SCIMProviderGroup):
        """Update existing group"""
        scim_group = self.to_schema(group, connection)
        scim_group.id = connection.scim_id
        try:
            self._request(
                "PUT",
                f"/Groups/{connection.scim_id}",
                json=scim_group.model_dump(
                    mode="json",
                    exclude_unset=True,
                ),
            )
            users = list(group.users.order_by("id").values_list("id", flat=True))
            return self._patch_add_users(group, users)
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise
        except (SCIMRequestException, ObjectExistsSyncException):
            # Some providers don't support PUT on groups, so this is mainly a fix for the initial
            # sync, send patch add requests for all the users the group currently has
            users = list(group.users.order_by("id").values_list("id", flat=True))
            self._patch_add_users(group, users)
            # Also update the group name
            return self._patch(
                scim_group.id,
                PatchOperation(
                    op=PatchOp.replace,
                    path="displayName",
                    value=scim_group.displayName,
                ),
            )

    def update_group(self, group: Group, action: Direction, users_set: set[int]):
        """Update a group, either using PUT to replace it or PATCH if supported"""
        if self._config.patch.supported:
            if action == Direction.add:
                return self._patch_add_users(group, users_set)
            if action == Direction.remove:
                return self._patch_remove_users(group, users_set)
        try:
            return self.write(group)
        except SCIMRequestException as exc:
            if self._config.is_fallback:
                # Assume that provider does not support PUT and also doesn't support
                # ServiceProviderConfig, so try PATCH as a fallback
                if action == Direction.add:
                    return self._patch_add_users(group, users_set)
                if action == Direction.remove:
                    return self._patch_remove_users(group, users_set)
            raise exc

    def _patch(
        self,
        group_id: str,
        *ops: PatchOperation,
    ):
        chunk_size = self._config.bulk.maxOperations
        if chunk_size < 1:
            chunk_size = len(ops)
        for chunk in batched(ops, chunk_size):
            req = PatchRequest(Operations=list(chunk))
            self._request(
                "PATCH",
                f"/Groups/{group_id}",
                json=req.model_dump(
                    mode="json",
                ),
            )

    def _patch_add_users(self, group: Group, users_set: set[int]):
        """Add users in users_set to group"""
        if len(users_set) < 1:
            return
        scim_group = SCIMProviderGroup.objects.filter(provider=self.provider, group=group).first()
        if not scim_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            SCIMProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("scim_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(
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

    def _patch_remove_users(self, group: Group, users_set: set[int]):
        """Remove users in users_set from group"""
        if len(users_set) < 1:
            return
        scim_group = SCIMProviderGroup.objects.filter(provider=self.provider, group=group).first()
        if not scim_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            SCIMProviderUser.objects.filter(
                user__pk__in=users_set, provider=self.provider
            ).values_list("scim_id", flat=True)
        )
        if len(user_ids) < 1:
            return
        self._patch(
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
