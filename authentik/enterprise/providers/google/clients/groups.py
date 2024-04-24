from deepmerge import always_merger
from django.db import transaction

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import Group
from authentik.enterprise.providers.google.clients.base import GoogleSyncClient
from authentik.enterprise.providers.google.models import (
    GoogleProviderGroup,
    GoogleProviderMapping,
)
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.exceptions import NotFoundSyncException, StopSync
from authentik.lib.utils.errors import exception_to_string


class GoogleGroupClient(GoogleSyncClient[Group, dict]):
    """Google client for groups"""

    def write(self, obj: Group):
        """Write a group"""
        google_group = GoogleProviderGroup.objects.filter(provider=self.provider, group=obj).first()
        if not google_group:
            return self._create(obj)
        try:
            return self._update(obj, google_group)
        except NotFoundSyncException:
            google_group.delete()
            return self._create(obj)

    def delete(self, obj: Group):
        """Delete group"""
        google_group = GoogleProviderGroup.objects.filter(provider=self.provider, group=obj).first()
        if not google_group:
            self.logger.debug("Group does not exist in Google, skipping")
            return None
        with transaction.atomic():
            response = self._request(
                self.directory_service.groups().delete(groupKey=google_group.id)
            )
            google_group.delete()
            return response

    def to_schema(self, obj: Group) -> dict:
        """Convert authentik group"""
        raw_google_group = {}
        for mapping in (
            self.provider.property_mappings_group.all().order_by("name").select_subclasses()
        ):
            if not isinstance(mapping, GoogleProviderMapping):
                continue
            try:
                mapping: GoogleProviderMapping
                value = mapping.evaluate(
                    user=None,
                    request=None,
                    group=obj,
                    provider=self.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_google_group, value)
            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping {exception_to_string(exc)}",
                    mapping=mapping,
                ).save()
                raise StopSync(exc, obj, mapping) from exc
        if not raw_google_group:
            raise StopSync(ValueError("No group mappings configured"), obj)

        return raw_google_group

    def _create(self, group: Group):
        """Create group from scratch and create a connection object"""
        google_group = self.to_schema(group)
        with transaction.atomic():
            response = self._request(self.directory_service.groups().insert(body=google_group))
            GoogleProviderGroup.objects.create(
                provider=self.provider, group=group, id=response["id"]
            )

    def _update(self, group: Group, connection: GoogleProviderGroup):
        """Update existing group"""
        google_group = self.to_schema(group)
        try:
            return self._request(self.directory_service.groups().update(
                groupKey=connection.id,
                body=google_group,
            ))
        except NotFoundSyncException:
            # Resource missing is handled by self.write, which will re-create the group
            raise
