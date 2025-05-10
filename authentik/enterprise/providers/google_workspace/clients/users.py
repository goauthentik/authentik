from django.db import transaction

from authentik.common.sync.mapper import PropertyMappingManager
from authentik.common.sync.outgoing.exceptions import (
    ObjectExistsSyncException,
    TransientSyncException,
)
from authentik.common.sync.outgoing.models import OutgoingSyncDeleteAction
from authentik.core.models import User
from authentik.enterprise.providers.google_workspace.clients.base import GoogleWorkspaceSyncClient
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceProvider,
    GoogleWorkspaceProviderMapping,
    GoogleWorkspaceProviderUser,
)
from authentik.policies.utils import delete_none_values


class GoogleWorkspaceUserClient(GoogleWorkspaceSyncClient[User, GoogleWorkspaceProviderUser, dict]):
    """Sync authentik users into google workspace"""

    connection_type = GoogleWorkspaceProviderUser
    connection_type_query = "user"
    can_discover = True

    def __init__(self, provider: GoogleWorkspaceProvider) -> None:
        super().__init__(provider)
        self.mapper = PropertyMappingManager(
            self.provider.property_mappings.all().order_by("name").select_subclasses(),
            GoogleWorkspaceProviderMapping,
            ["provider", "connection"],
        )

    def to_schema(self, obj: User, connection: GoogleWorkspaceProviderUser) -> dict:
        """Convert authentik user"""
        return delete_none_values(super().to_schema(obj, connection, primaryEmail=obj.email))

    def delete(self, obj: User):
        """Delete user"""
        google_user = GoogleWorkspaceProviderUser.objects.filter(
            provider=self.provider, user=obj
        ).first()
        if not google_user:
            self.logger.debug("User does not exist in Google, skipping")
            return None
        with transaction.atomic():
            response = None
            if self.provider.user_delete_action == OutgoingSyncDeleteAction.DELETE:
                response = self._request(
                    self.directory_service.users().delete(userKey=google_user.google_id)
                )
            elif self.provider.user_delete_action == OutgoingSyncDeleteAction.SUSPEND:
                response = self._request(
                    self.directory_service.users().update(
                        userKey=google_user.google_id, body={"suspended": True}
                    )
                )
            google_user.delete()
        return response

    def create(self, user: User):
        """Create user from scratch and create a connection object"""
        google_user = self.to_schema(user, None)
        self.check_email_valid(
            google_user["primaryEmail"], *[x["address"] for x in google_user.get("emails", [])]
        )
        with transaction.atomic():
            try:
                response = self._request(self.directory_service.users().insert(body=google_user))
            except ObjectExistsSyncException:
                # user already exists in google workspace, so we can connect them manually
                return GoogleWorkspaceProviderUser.objects.create(
                    provider=self.provider, user=user, google_id=user.email, attributes={}
                )
            except TransientSyncException as exc:
                raise exc
            else:
                return GoogleWorkspaceProviderUser.objects.create(
                    provider=self.provider,
                    user=user,
                    google_id=response["primaryEmail"],
                    attributes=response,
                )

    def update(self, user: User, connection: GoogleWorkspaceProviderUser):
        """Update existing user"""
        google_user = self.to_schema(user, connection)
        self.check_email_valid(
            google_user["primaryEmail"], *[x["address"] for x in google_user.get("emails", [])]
        )
        response = self._request(
            self.directory_service.users().update(userKey=connection.google_id, body=google_user)
        )
        connection.attributes = response
        connection.save()

    def discover(self):
        """Iterate through all users and connect them with authentik users if possible"""
        request = self.directory_service.users().list(
            customer="my_customer", maxResults=500, orderBy="email"
        )
        while request:
            response = request.execute()
            for user in response.get("users", []):
                self._discover_single_user(user)
            request = self.directory_service.users().list_next(
                previous_request=request, previous_response=response
            )

    def _discover_single_user(self, user: dict):
        """handle discovery of a single user"""
        email = user["primaryEmail"]
        matching_authentik_user = self.provider.get_object_qs(User).filter(email=email).first()
        if not matching_authentik_user:
            return
        GoogleWorkspaceProviderUser.objects.get_or_create(
            provider=self.provider,
            user=matching_authentik_user,
            google_id=email,
            attributes=user,
        )

    def update_single_attribute(self, connection: GoogleWorkspaceProviderUser):
        user = self.directory_service.users().get(connection.google_id)
        connection.attributes = user
