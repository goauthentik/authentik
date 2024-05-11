"""Group client"""

from deepmerge import always_merger
from pydantic import ValidationError
from pydanticscim.group import GroupMember
from pydanticscim.responses import PatchOp, PatchOperation

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
    SkipObjectException,
)
from authentik.core.models import Group
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsSyncException,
    StopSync,
)
from authentik.lib.sync.outgoing.mapper import PropertyMappingManager
from authentik.lib.utils.errors import exception_to_string
from authentik.policies.utils import delete_none_values
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import (
    SCIMRequestException,
)
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA, PatchRequest
from authentik.providers.scim.clients.schema import Group as SCIMGroupSchema
from authentik.providers.scim.models import SCIMGroup, SCIMMapping, SCIMProvider, SCIMUser


class SCIMGroupClient(SCIMClient[Group, SCIMGroup, SCIMGroupSchema]):
    """SCIM client for groups"""

    connection_type = SCIMGroup
    connection_type_query = "group"
    mapper: PropertyMappingManager

    def __init__(self, provider: SCIMProvider):
        super().__init__(provider)
        self.mapper = PropertyMappingManager(
            self.provider.property_mappings_group.all().order_by("name").select_subclasses(),
            SCIMMapping,
            ["group", "provider", "creating"],
        )

    def to_schema(self, obj: Group, creating: bool) -> SCIMGroupSchema:
        """Convert authentik user into SCIM"""
        raw_scim_group = {
            "schemas": (SCIM_GROUP_SCHEMA,),
        }
        try:
            for value in self.mapper.iter_eval(
                user=None,
                request=None,
                group=obj,
                provider=self.provider,
                creating=creating,
            ):
                try:
                    always_merger.merge(raw_scim_group, value)
                except SkipObjectException as exc:
                    raise exc from exc
        except PropertyMappingExpressionException as exc:
            # Value error can be raised when assigning invalid data to an attribute
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to evaluate property-mapping {exception_to_string(exc)}",
                mapping=exc.mapping,
            ).save()
            raise StopSync(exc, obj, exc.mapping) from exc
        if not raw_scim_group:
            raise StopSync(ValueError("No group mappings configured"), obj)
        try:
            scim_group = SCIMGroupSchema.model_validate(delete_none_values(raw_scim_group))
        except ValidationError as exc:
            raise StopSync(exc, obj) from exc
        if not scim_group.externalId:
            scim_group.externalId = str(obj.pk)

        users = list(obj.users.order_by("id").values_list("id", flat=True))
        connections = SCIMUser.objects.filter(provider=self.provider, user__pk__in=users)
        members = []
        for user in connections:
            members.append(
                GroupMember(
                    value=user.scim_id,
                )
            )
        if members:
            scim_group.members = members
        return scim_group

    def delete(self, obj: Group):
        """Delete group"""
        scim_group = SCIMGroup.objects.filter(provider=self.provider, group=obj).first()
        if not scim_group:
            self.logger.debug("Group does not exist in SCIM, skipping")
            return None
        response = self._request("DELETE", f"/Groups/{scim_group.scim_id}")
        scim_group.delete()
        return response

    def create(self, group: Group):
        """Create group from scratch and create a connection object"""
        scim_group = self.to_schema(group, True)
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
        return SCIMGroup.objects.create(provider=self.provider, group=group, scim_id=scim_id)

    def update(self, group: Group, connection: SCIMGroup):
        """Update existing group"""
        scim_group = self.to_schema(group, False)
        scim_group.id = connection.scim_id
        try:
            return self._request(
                "PUT",
                f"/Groups/{connection.scim_id}",
                json=scim_group.model_dump(
                    mode="json",
                    exclude_unset=True,
                ),
            )
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
        req = PatchRequest(Operations=ops)
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
        scim_group = SCIMGroup.objects.filter(provider=self.provider, group=group).first()
        if not scim_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            SCIMUser.objects.filter(user__pk__in=users_set, provider=self.provider).values_list(
                "scim_id", flat=True
            )
        )
        if len(user_ids) < 1:
            return
        self._patch(
            scim_group.scim_id,
            PatchOperation(
                op=PatchOp.add,
                path="members",
                value=[{"value": x} for x in user_ids],
            ),
        )

    def _patch_remove_users(self, group: Group, users_set: set[int]):
        """Remove users in users_set from group"""
        if len(users_set) < 1:
            return
        scim_group = SCIMGroup.objects.filter(provider=self.provider, group=group).first()
        if not scim_group:
            self.logger.warning(
                "could not sync group membership, group does not exist", group=group
            )
            return
        user_ids = list(
            SCIMUser.objects.filter(user__pk__in=users_set, provider=self.provider).values_list(
                "scim_id", flat=True
            )
        )
        if len(user_ids) < 1:
            return
        self._patch(
            scim_group.scim_id,
            PatchOperation(
                op=PatchOp.remove,
                path="members",
                value=[{"value": x} for x in user_ids],
            ),
        )
