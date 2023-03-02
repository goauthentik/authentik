"""Group client"""
from pydanticscim.group import GroupMember

from authentik.core.models import Group
from authentik.providers.scim.clients import PAGE_SIZE
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.schema import Group as SCIMGroupSchema
from authentik.providers.scim.models import SCIMGroup, SCIMUser


class SCIMGroupClient:
    """SCIM client for groups"""

    _client: SCIMClient

    def __init__(self, client: SCIMClient) -> None:
        self._client = client

    def write(self, group: Group):
        """Write a group"""
        scim_group = SCIMGroup.objects.filter(provider=self._client.provider, group=group).first()
        if not scim_group:
            return self._create(group)
        return None

    def delete(self, group: Group):
        """Delete group"""
        scim_group = SCIMGroup.objects.filter(provider=self._client.provider, group=group).first()
        if not scim_group:
            self._client.logger.debug("Group does not exist in SCIM, skipping")
            return None
        response = self._client._request("DELETE", f"/Groups/{scim_group.id}")
        scim_group.delete()
        return response

    def to_scim(self, group: Group) -> SCIMGroupSchema:
        """Convert authentik user into SCIM"""
        # TODO: property mappings
        scim_group = SCIMGroupSchema(displayName=group.name, externalId=str(group.pk), members=[])
        users = list(group.users.order_by("id").values_list("id", flat=True))
        connections = SCIMUser.objects.filter(provider=self._client.provider, user__pk__in=users)[
            :PAGE_SIZE
        ]
        for user in connections:
            scim_group.members.append(
                GroupMember(
                    value=user.id,
                )
            )
        return scim_group

    def _create(self, group: Group):
        """Create group from scratch and create a connection object"""
        scim_group = self.to_scim(group)
        response = self._client._request(
            "POST",
            "/Groups",
            data=scim_group.json(
                exclude_unset=True,
            ),
        )
        SCIMGroup.objects.create(provider=self._client.provider, group=group, id=response["id"])
