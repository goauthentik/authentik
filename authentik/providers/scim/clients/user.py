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


class SCIMUserClient(SCIMClient[User]):
    """SCIM client for users"""

    def write(self, obj: User):
        """Write a user"""
        scim_user = SCIMUser.objects.filter(provider=self.provider, user=obj).first()
        if not scim_user:
            return self._create(obj)
        return self._update(obj, scim_user)

    def delete(self, obj: User):
        """Delete user"""
        scim_user = SCIMUser.objects.filter(provider=self.provider, user=obj).first()
        if not scim_user:
            self.logger.debug("User does not exist in SCIM, skipping")
            return None
        response = self._request("DELETE", f"/Users/{scim_user.id}")
        scim_user.delete()
        return response

    def to_scim(self, user: User) -> SCIMUserSchema:
        """Convert authentik user into SCIM"""
        raw_scim_user = {}
        for mapping in self.provider.property_mappings.all().order_by("name").select_subclasses():
            if not isinstance(mapping, SCIMMapping):
                continue
            try:
                mapping: SCIMMapping
                value = mapping.evaluate(
                    user=user,
                    request=None,
                    provider=self.provider,
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
                raise StopSync(exc, user, mapping) from exc
        try:
            scim_user = SCIMUserSchema.parse_obj(raw_scim_user)
        except ValidationError as exc:
            raise StopSync(exc, user) from exc
        return scim_user

    def _create(self, user: User):
        """Create user from scratch and create a connection object"""
        scim_user = self.to_scim(user)
        response = self._request(
            "POST",
            "/Users",
            data=scim_user.json(
                exclude_unset=True,
            ),
        )
        SCIMUser.objects.create(provider=self.provider, user=user, id=response["id"])

    def _update(self, user: User, connection: SCIMUser):
        """Update existing user"""
        scim_user = self.to_scim(user)
        scim_user.id = connection.id
        self._request(
            "PUT",
            f"/Users/{connection.id}",
            data=scim_user.json(
                exclude_unset=True,
            ),
        )
