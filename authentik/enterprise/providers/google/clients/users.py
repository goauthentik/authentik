from deepmerge import always_merger
from django.db import transaction

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import User
from authentik.enterprise.providers.google.clients.base import GoogleSyncClient
from authentik.enterprise.providers.google.models import GoogleProviderMapping, GoogleProviderUser
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.exceptions import NotFoundSyncException, StopSync
from authentik.lib.utils.errors import exception_to_string
from authentik.policies.utils import delete_none_values


class GoogleUserClient(GoogleSyncClient[User, dict]):
    """Sync authentik users into google workspace"""

    def write(self, obj: User):
        """Write a user"""
        google_user = GoogleProviderUser.objects.filter(provider=self.provider, user=obj).first()
        if not google_user:
            return self._create(obj)
        try:
            return self._update(obj, google_user)
        except NotFoundSyncException:
            google_user.delete()
            return self._create(obj)

    def delete(self, obj: User):
        """Delete user"""
        google_user = GoogleProviderUser.objects.filter(provider=self.provider, user=obj).first()
        if not google_user:
            self.logger.debug("User does not exist in Google, skipping")
            return None
        with transaction.atomic():
            # TODO: Delete vs suspend
            response = self._request(self.directory_service.users().delete(userKey=google_user.id))
            google_user.delete()
        return response

    def to_schema(self, obj: User) -> dict:
        """Convert authentik user"""
        raw_google_user = {}
        for mapping in self.provider.property_mappings.all().order_by("name").select_subclasses():
            if not isinstance(mapping, GoogleProviderMapping):
                continue
            try:
                mapping: GoogleProviderMapping
                value = mapping.evaluate(
                    user=obj,
                    request=None,
                    provider=self.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_google_user, value)
            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping {exception_to_string(exc)}",
                    mapping=mapping,
                ).save()
                raise StopSync(exc, obj, mapping) from exc
        if not raw_google_user:
            raise StopSync(ValueError("No user mappings configured"), obj)
        if "primaryEmail" not in raw_google_user:
            raw_google_user["primaryEmail"] = str(obj.email)
        return delete_none_values(raw_google_user)

    def _create(self, user: User):
        """Create user from scratch and create a connection object"""
        google_user = self.to_schema(user)
        with transaction.atomic():
            response = self._request(self.directory_service.users().insert(body=google_user))
            GoogleProviderUser.objects.create(
                provider=self.provider, user=user, id=response["primaryEmail"]
            )

    def _update(self, user: User, connection: GoogleProviderUser):
        """Update existing user"""
        google_user = self.to_schema(user)
        google_user[""] = connection.id
        self._request(
            self.directory_service.users().update(userKey=connection.id, body=google_user)
        )
