from deepmerge import always_merger
from django.db import transaction
from msgraph.generated.models.user import User as MSUser
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
    SkipObjectException,
)
from authentik.core.models import User
from authentik.enterprise.providers.microsoft_entra.clients.base import MicrosoftEntraSyncClient
from authentik.enterprise.providers.microsoft_entra.models import (
    MicrosoftEntraProviderMapping,
    MicrosoftEntraProviderUser,
)
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.exceptions import (
    ObjectExistsSyncException,
    StopSync,
    TransientSyncException,
)
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction
from authentik.lib.utils.errors import exception_to_string
from authentik.policies.utils import delete_none_values


class MicrosoftEntraUserClient(MicrosoftEntraSyncClient[User, MicrosoftEntraProviderUser, MSUser]):
    """Sync authentik users into microsoft entra"""

    connection_type = MicrosoftEntraProviderUser
    connection_type_query = "user"
    can_discover = True

    def to_schema(self, obj: User) -> MSUser:
        """Convert authentik user"""
        raw_microsoft_user = {}
        for mapping in self.provider.property_mappings.all().order_by("name").select_subclasses():
            if not isinstance(mapping, MicrosoftEntraProviderMapping):
                continue
            try:
                value = mapping.evaluate(
                    user=obj,
                    request=None,
                    provider=self.provider,
                )
                if value is None:
                    continue
                always_merger.merge(raw_microsoft_user, value)
            except SkipObjectException as exc:
                raise exc from exc
            except (PropertyMappingExpressionException, ValueError) as exc:
                # Value error can be raised when assigning invalid data to an attribute
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping {exception_to_string(exc)}",
                    mapping=mapping,
                ).save()
                raise StopSync(exc, obj, mapping) from exc
        if not raw_microsoft_user:
            raise StopSync(ValueError("No user mappings configured"), obj)
        return MSUser(**delete_none_values(raw_microsoft_user))

    def delete(self, obj: User):
        """Delete user"""
        microsoft_user = MicrosoftEntraProviderUser.objects.filter(
            provider=self.provider, user=obj
        ).first()
        if not microsoft_user:
            self.logger.debug("User does not exist in Microsoft, skipping")
            return None
        with transaction.atomic():
            response = None
            if self.provider.user_delete_action == OutgoingSyncDeleteAction.DELETE:
                response = self._request(
                    self.client.users.by_user_id(microsoft_user.microsoft_id).delete()
                )
            elif self.provider.user_delete_action == OutgoingSyncDeleteAction.SUSPEND:
                response = self._request(
                    self.client.users.by_user_id(microsoft_user.microsoft_id).patch(MSUser(account_enabled=False))
                )
            microsoft_user.delete()
        return response

    def create(self, user: User):
        """Create user from scratch and create a connection object"""
        microsoft_user = self.to_schema(user)
        # self.check_email_valid(
        #     microsoft_user["primaryEmail"],
        #     *[x["address"] for x in microsoft_user.get("emails", [])],
        # )
        with transaction.atomic():
            try:
                response = self._request(self.client.users.post(microsoft_user))
            except ObjectExistsSyncException:
                # user already exists in microsoft entra, so we can connect them manually
                query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters()(
                    filter=f"mail eq '{microsoft_user.mail}'",
                )
                request_configuration = (
                    UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                        query_parameters=query_params,
                    )
                )
                user_data = self._request(self.client.users.get(request_configuration))
                if user_data.odata_count < 1:
                    self.logger.warning(
                        "User which could not be created also does not exist", user=user
                    )
                    return
                MicrosoftEntraProviderUser.objects.create(
                    provider=self.provider, user=user, microsoft_id=user_data.value[0].id
                )
            except TransientSyncException as exc:
                raise exc
            else:
                MicrosoftEntraProviderUser.objects.create(
                    provider=self.provider, user=user, microsoft_id=response.id
                )

    def update(self, user: User, connection: MicrosoftEntraProviderUser):
        """Update existing user"""
        microsoft_user = self.to_schema(user)
        # self.check_email_valid(
        #     microsoft_user["primaryEmail"],
        #     *[x["address"] for x in microsoft_user.get("emails", [])],
        # )
        self._request(self.client.users.by_user_id(connection.microsoft_id).patch(microsoft_user))

    def discover(self):
        """Iterate through all users and connect them with authentik users if possible"""
        users = self._request(self.client.users.get())
        next_link = True
        while next_link:
            for user in users.value:
                self._discover_single_user(user)
            next_link = users.odata_next_link
            if not next_link:
                break
            users = self._request(self.client.users.with_url(next_link).get())

    def _discover_single_user(self, user: MSUser):
        """handle discovery of a single user"""
        matching_authentik_user = self.provider.get_object_qs(User).filter(email=user.mail).first()
        if not matching_authentik_user:
            return
        MicrosoftEntraProviderUser.objects.get_or_create(
            provider=self.provider,
            user=matching_authentik_user,
            microsoft_id=user.id,
        )
