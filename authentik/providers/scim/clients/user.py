"""User client"""
from pydanticscim.user import Email, EmailKind, Name, Photo, PhotoKind

from authentik.core.models import User
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.schema import User as SCIMUserSchema
from authentik.providers.scim.models import SCIMUser


class SCIMUserClient:
    """SCIM client for users"""

    _client: SCIMClient

    def __init__(self, client: SCIMClient) -> None:
        self._client = client

    def write_user(self, user: User):
        """Write a user"""
        scim_user = SCIMUser.objects.filter(provider=self._client.provider, user=user).first()
        if not scim_user:
            return self._create_user(user)
        return self._update_user(user, scim_user)

    def delete_user(self, user: User):
        """Delete user"""
        scim_user = SCIMUser.objects.filter(provider=self._client.provider, user=user).first()
        if not scim_user:
            self._client.logger.debug("User does not exist in SCIM, skipping")
            return None
        response = self._client._request("DELETE", f"/Users/{scim_user.id}")
        scim_user.delete()
        return response

    def _scim_user(self, user: User) -> SCIMUserSchema:
        """Convert authentik user into SCIM"""
        # TODO: property mappings
        scim_user = SCIMUserSchema(
            userName=user.username,
            externalId=user.uid,
            name=Name(
                formatted=user.name,
                # TODO use mapping for this
                givenName=user.name.split(" ")[0],
                familyName=user.name.split(" ")[1],
            ),
            displayName=user.name,
            active=user.is_active,
            emails=[Email(value=user.email, type=EmailKind.other, primary=True)],
        )
        avatar = user.avatar
        if "://" in avatar:
            scim_user.photos = [Photo(value=avatar, type=PhotoKind.photo)]
        locale = user.locale()
        if locale != "":
            scim_user.locale = locale
        return scim_user

    def _create_user(self, user: User):
        """Create user from scratch and create a connection object"""
        scim_user = self._scim_user(user)
        response = self._client._request(
            "POST",
            "/Users",
            data=scim_user.json(
                exclude_unset=True,
            ),
        )
        SCIMUser.objects.create(provider=self._client.provider, user=user, id=response["id"])

    def _update_user(self, user: User, connection: SCIMUser):
        """Update existing user"""
        scim_user = self._scim_user(user)
        scim_user.id = connection.id
        self._client._request(
            "PUT",
            f"/Users/{connection.id}",
            data=scim_user.json(
                exclude_unset=True,
            ),
        )
