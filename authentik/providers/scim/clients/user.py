"""User client"""
from deepmerge import always_merger
from pydantic import ValidationError

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import StopSync
from authentik.providers.scim.clients.schema import User as SCIMUserSchema
from authentik.providers.scim.models import SCIMMapping, SCIMUser


class SCIMUserClient:
    """SCIM client for users"""

    _client: SCIMClient

    def __init__(self, client: SCIMClient) -> None:
        self._client = client

    def write(self, user: User):
        """Write a user"""
        scim_user = SCIMUser.objects.filter(provider=self._client.provider, user=user).first()
        if not scim_user:
            return self._create(user)
        return self._update(user, scim_user)

    def delete(self, user: User):
        """Delete user"""
        scim_user = SCIMUser.objects.filter(provider=self._client.provider, user=user).first()
        if not scim_user:
            self._client.logger.debug("User does not exist in SCIM, skipping")
            return None
        response = self._client._request("DELETE", f"/Users/{scim_user.id}")
        scim_user.delete()
        return response

    def to_scim(self, user: User) -> SCIMUserSchema:
        """Convert authentik user into SCIM"""
        raw_scim_user = {}
        for mapping in (
            self._client.provider.property_mappings.all().order_by("name").select_subclasses()
        ):
            if not isinstance(mapping, SCIMMapping):
                continue
            try:
                mapping: SCIMMapping
                value = mapping.evaluate(
                    user=user,
                    provider=self._client.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_scim_user, value)
            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping: {str(exc)}",
                    mapping=mapping,
                ).save()
                raise StopSync(exc) from exc
        try:
            scim_user = SCIMUserSchema.parse_obj(raw_scim_user)
        except ValidationError as exc:
            raise StopSync(exc) from exc
        return scim_user

    def _create(self, user: User):
        """Create user from scratch and create a connection object"""
        scim_user = self.to_scim(user)
        response = self._client._request(
            "POST",
            "/Users",
            data=scim_user.json(
                exclude_unset=True,
            ),
        )
        SCIMUser.objects.create(provider=self._client.provider, user=user, id=response["id"])

    def _update(self, user: User, connection: SCIMUser):
        """Update existing user"""
        scim_user = self.to_scim(user)
        scim_user.id = connection.id
        self._client._request(
            "PUT",
            f"/Users/{connection.id}",
            data=scim_user.json(
                exclude_unset=True,
            ),
        )
