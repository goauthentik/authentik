"""Group client"""
from deepmerge import always_merger
from pydantic import ValidationError
from pydanticscim.group import GroupMember

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import Group
from authentik.events.models import Event, EventAction
from authentik.providers.scim.clients import PAGE_SIZE
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import StopSync
from authentik.providers.scim.clients.schema import Group as SCIMGroupSchema
from authentik.providers.scim.models import SCIMGroup, SCIMMapping, SCIMUser


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
        raw_scim_group = {}
        for mapping in (
            self._client.provider.property_mappings_group.all().order_by("name").select_subclasses()
        ):
            if not isinstance(mapping, SCIMMapping):
                continue
            try:
                mapping: SCIMMapping
                value = mapping.evaluate(
                    user=None,
                    request=None,
                    group=group,
                    provider=self._client.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_scim_group, value)
            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping: {str(exc)}",
                    mapping=mapping,
                ).save()
                raise StopSync(exc, group, mapping) from exc
        try:
            scim_group = SCIMGroupSchema.parse_obj(raw_scim_group)
        except ValidationError as exc:
            raise StopSync(exc, group) from exc
        scim_group.externalId = str(group.pk)

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
