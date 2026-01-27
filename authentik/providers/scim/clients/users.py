"""User client"""

from typing import Any

from django.db import transaction
from django.utils.http import urlencode
from orjson import dumps
from pydantic import ValidationError

from authentik.core.models import User
from authentik.lib.merge import MERGE_LIST_UNIQUE
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.lib.sync.outgoing.exceptions import ObjectExistsSyncException, StopSync
from authentik.policies.utils import delete_none_values
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.schema import SCIM_USER_SCHEMA
from authentik.providers.scim.clients.schema import User as SCIMUserSchema
from authentik.providers.scim.models import SCIMMapping, SCIMProvider, SCIMProviderUser


class SCIMUserClient(SCIMClient[User, SCIMProviderUser, SCIMUserSchema]):
    """SCIM client for users"""

    connection_type = SCIMProviderUser
    connection_type_query = "user"
    mapper: PropertyMappingManager

    def __init__(self, provider: SCIMProvider):
        super().__init__(provider)
        self.mapper = PropertyMappingManager(
            self.provider.property_mappings.all().order_by("name").select_subclasses(),
            SCIMMapping,
            ["provider", "connection"],
        )

    def to_schema(self, obj: User, connection: SCIMProviderUser) -> SCIMUserSchema:
        """Convert authentik user into SCIM"""
        raw_scim_user = super().to_schema(obj, connection)
        try:
            scim_user = SCIMUserSchema.model_validate(delete_none_values(raw_scim_user))
        except ValidationError as exc:
            raise StopSync(exc, obj) from exc
        if SCIM_USER_SCHEMA not in scim_user.schemas:
            scim_user.schemas.insert(0, SCIM_USER_SCHEMA)
        # As this might be unset, we need to tell pydantic it's set so ensure the schemas
        # are included, even if its just the defaults
        scim_user.schemas = list(scim_user.schemas)
        if not scim_user.externalId:
            scim_user.externalId = str(obj.uid)
        return scim_user

    def delete(self, identifier: str):
        """Delete user"""
        SCIMProviderUser.objects.filter(provider=self.provider, scim_id=identifier).delete()
        return self._request("DELETE", f"/Users/{identifier}")

    def create(self, user: User):
        """Create user from scratch and create a connection object"""
        scim_user = self.to_schema(user, None)
        with transaction.atomic():
            try:
                response = self._request(
                    "POST",
                    "/Users",
                    json=scim_user.model_dump(
                        mode="json",
                        exclude_unset=True,
                    ),
                )
            except ObjectExistsSyncException as exc:
                if not self._config.filter.supported:
                    raise exc
                users = self._request(
                    "GET",
                    f"/Users?{urlencode({'filter': f'userName eq "{scim_user.userName}"'})}",
                )
                users_res = users.get("Resources", [])
                if len(users_res) < 1:
                    raise exc
                return SCIMProviderUser.objects.create(
                    provider=self.provider,
                    user=user,
                    scim_id=users_res[0]["id"],
                    attributes=users_res[0],
                )
            else:
                scim_id = response.get("id")
                if not scim_id or scim_id == "":
                    raise StopSync("SCIM Response with missing or invalid `id`")
                return SCIMProviderUser.objects.create(
                    provider=self.provider, user=user, scim_id=scim_id, attributes=response
                )

    def diff(self, local_created: dict[str, Any], connection: SCIMProviderUser):
        """Check if a user is different than what we last wrote to the remote system.
        Returns true if there is a difference in data."""
        local_known = connection.attributes
        local_updated = {}
        MERGE_LIST_UNIQUE.merge(local_updated, local_known)
        MERGE_LIST_UNIQUE.merge(local_updated, local_created)
        return dumps(local_updated) != dumps(local_known)

    def update(self, user: User, connection: SCIMProviderUser):
        """Update existing user"""
        scim_user = self.to_schema(user, connection)
        scim_user.id = connection.scim_id
        payload = scim_user.model_dump(
            mode="json",
            exclude_unset=True,
        )
        if not self.diff(payload, connection):
            self.logger.debug("Skipping user write as data has not changed")
            return
        response = self._request(
            "PUT",
            f"/Users/{connection.scim_id}",
            json=payload,
        )
        connection.attributes = response
        connection.save()
