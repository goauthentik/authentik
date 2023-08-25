"""Group client"""
from deepmerge import always_merger
from pydantic import ValidationError
from pydanticscim.group import GroupMember
from pydanticscim.responses import PatchOp, PatchOperation

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import Group
from authentik.events.models import Event, EventAction
from authentik.lib.utils.errors import exception_to_string
from authentik.policies.utils import delete_none_values
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import (
    ResourceMissing,
    SCIMRequestException,
    StopSync,
)
from authentik.providers.scim.clients.schema import Group as SCIMGroupSchema
from authentik.providers.scim.clients.schema import PatchRequest
from authentik.providers.scim.models import SCIMGroup, SCIMMapping, SCIMUser


class SCIMGroupClient(SCIMClient[Group, SCIMGroupSchema]):
    """SCIM client for groups"""

    def write(self, obj: Group):
        """Write a group"""
        scim_group = SCIMGroup.objects.filter(provider=self.provider, group=obj).first()
        if not scim_group:
            return self._create(obj)
        try:
            return self._update(obj, scim_group)
        except ResourceMissing:
            scim_group.delete()
            return self._create(obj)

    def delete(self, obj: Group):
        """Delete group"""
        scim_group = SCIMGroup.objects.filter(provider=self.provider, group=obj).first()
        if not scim_group:
            self.logger.debug("Group does not exist in SCIM, skipping")
            return None
        response = self._request("DELETE", f"/Groups/{scim_group.id}")
        scim_group.delete()
        return response

    def to_scim(self, obj: Group) -> SCIMGroupSchema:
        """Convert authentik user into SCIM"""
        raw_scim_group = {}
        for mapping in (
            self.provider.property_mappings_group.all().order_by("name").select_subclasses()
        ):
            if not isinstance(mapping, SCIMMapping):
                continue
            try:
                mapping: SCIMMapping
                value = mapping.evaluate(
                    user=None,
                    request=None,
                    group=obj,
                    provider=self.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_scim_group, value)
            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping {exception_to_string(exc)}",
                    mapping=mapping,
                ).save()
                raise StopSync(exc, obj, mapping) from exc
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
                    value=user.id,
                )
            )
        if members:
            scim_group.members = members
        return scim_group

    def _create(self, group: Group):
        """Create group from scratch and create a connection object"""
        scim_group = self.to_scim(group)
        response = self._request(
            "POST",
            "/Groups",
            json=scim_group.model_dump(
                mode="json",
                exclude_unset=True,
            ),
        )
        SCIMGroup.objects.create(provider=self.provider, group=group, id=response["id"])

    def _update(self, group: Group, connection: SCIMGroup):
        """Update existing group"""
        scim_group = self.to_scim(group)
        scim_group.id = connection.id
        try:
            return self._request(
                "PUT",
                f"/Groups/{scim_group.id}",
                json=scim_group.model_dump(
                    mode="json",
                    exclude_unset=True,
                ),
            )
        except ResourceMissing:
            # Resource missing is handled by self.write, which will re-create the group
            raise
        except SCIMRequestException:
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

    def update_group(self, group: Group, action: PatchOp, users_set: set[int]):
        """Update a group, either using PUT to replace it or PATCH if supported"""
        if self._config.patch.supported:
            if action == PatchOp.add:
                return self._patch_add_users(group, users_set)
            if action == PatchOp.remove:
                return self._patch_remove_users(group, users_set)
        try:
            return self.write(group)
        except SCIMRequestException as exc:
            if self._config.is_fallback:
                # Assume that provider does not support PUT and also doesn't support
                # ServiceProviderConfig, so try PATCH as a fallback
                if action == PatchOp.add:
                    return self._patch_add_users(group, users_set)
                if action == PatchOp.remove:
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
                "id", flat=True
            )
        )
        if len(user_ids) < 1:
            return
        self._patch(
            scim_group.id,
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
                "id", flat=True
            )
        )
        if len(user_ids) < 1:
            return
        self._patch(
            scim_group.id,
            PatchOperation(
                op=PatchOp.remove,
                path="members",
                value=[{"value": x} for x in user_ids],
            ),
        )
