"""User client"""

from pydantic import ValidationError

from authentik.core.models import User
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.sync.outgoing.mapper import PropertyMappingManager
from authentik.policies.utils import delete_none_values
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.schema import SCIM_USER_SCHEMA
from authentik.providers.scim.clients.schema import User as SCIMUserSchema
from authentik.providers.scim.models import SCIMMapping, SCIMProvider, SCIMUser


class SCIMUserClient(SCIMClient[User, SCIMUser, SCIMUserSchema]):
    """SCIM client for users"""

    connection_type = SCIMUser
    connection_type_query = "user"
    mapper: PropertyMappingManager

    def __init__(self, provider: SCIMProvider):
        super().__init__(provider)
        self.mapper = PropertyMappingManager(
            self.provider.property_mappings.all().order_by("name").select_subclasses(),
            SCIMMapping,
            ["provider", "creating"],
        )

    def to_schema(self, obj: User, creating: bool) -> SCIMUserSchema:
        """Convert authentik user into SCIM"""
        raw_scim_user = super().to_schema(
            obj,
            creating,
            schemas=(SCIM_USER_SCHEMA,),
        )
        try:
            scim_user = SCIMUserSchema.model_validate(delete_none_values(raw_scim_user))
        except ValidationError as exc:
            raise StopSync(exc, obj) from exc
        if not scim_user.externalId:
            scim_user.externalId = str(obj.uid)
        return scim_user

    def delete(self, obj: User):
        """Delete user"""
        scim_user = SCIMUser.objects.filter(provider=self.provider, user=obj).first()
        if not scim_user:
            self.logger.debug("User does not exist in SCIM, skipping")
            return None
        response = self._request("DELETE", f"/Users/{scim_user.scim_id}")
        scim_user.delete()
        return response

    def create(self, user: User):
        """Create user from scratch and create a connection object"""
        scim_user = self.to_schema(user, True)
        response = self._request(
            "POST",
            "/Users",
            json=scim_user.model_dump(
                mode="json",
                exclude_unset=True,
            ),
        )
        scim_id = response.get("id")
        if not scim_id or scim_id == "":
            raise StopSync("SCIM Response with missing or invalid `id`")
        return SCIMUser.objects.create(provider=self.provider, user=user, scim_id=scim_id)

    def update(self, user: User, connection: SCIMUser):
        """Update existing user"""
        scim_user = self.to_schema(user, False)
        scim_user.id = connection.scim_id
        self._request(
            "PUT",
            f"/Users/{connection.scim_id}",
            json=scim_user.model_dump(
                mode="json",
                exclude_unset=True,
            ),
        )
