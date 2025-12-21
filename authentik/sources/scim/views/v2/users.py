"""SCIM User Views"""

from uuid import uuid4

from django.db.models import Q
from django.db.transaction import atomic
from django.http import QueryDict
from django.urls import reverse
from pydanticscim.user import Email, EmailKind, Name
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import User
from authentik.providers.scim.clients.schema import SCIM_USER_SCHEMA
from authentik.providers.scim.clients.schema import User as SCIMUserModel
from authentik.sources.scim.models import SCIMSourceUser
from authentik.sources.scim.patch.processor import SCIMPatchProcessor
from authentik.sources.scim.views.v2.base import SCIMObjectView
from authentik.sources.scim.views.v2.exceptions import SCIMConflictError, SCIMNotFoundError


class UsersView(SCIMObjectView):
    """SCIM User view"""

    model = User

    def user_to_scim(self, scim_user: SCIMSourceUser) -> dict:
        """Convert User to SCIM data"""
        payload = SCIMUserModel(
            schemas=[SCIM_USER_SCHEMA],
            id=str(scim_user.user.uuid),
            externalId=scim_user.external_id,
            userName=scim_user.user.username,
            name=Name(
                formatted=scim_user.user.name,
            ),
            displayName=scim_user.user.name,
            active=scim_user.user.is_active,
            emails=(
                [Email(value=scim_user.user.email, type=EmailKind.work, primary=True)]
                if scim_user.user.email
                else []
            ),
            meta={
                "resourceType": "User",
                "created": scim_user.user.date_joined,
                "lastModified": scim_user.last_update,
                "location": self.request.build_absolute_uri(
                    reverse(
                        "authentik_sources_scim:v2-users",
                        kwargs={
                            "source_slug": self.kwargs["source_slug"],
                            "user_id": str(scim_user.user.uuid),
                        },
                    )
                ),
            },
        )
        final_payload = payload.model_dump(mode="json", exclude_unset=True)
        final_payload.update(scim_user.attributes)
        return self.remove_excluded_attributes(
            SCIMUserModel.model_validate(final_payload).model_dump(mode="json", exclude_unset=True)
        )

    def get(self, request: Request, user_id: str | None = None, **kwargs) -> Response:
        """List User handler"""
        if user_id:
            connection = (
                SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id)
                .select_related("user")
                .first()
            )
            if not connection:
                raise SCIMNotFoundError("User not found.")
            return Response(self.user_to_scim(connection))
        connections = (
            SCIMSourceUser.objects.filter(source=self.source).select_related("user").order_by("pk")
        )
        connections = connections.filter(self.filter_parse(request))
        page = self.paginate_query(connections)
        return Response(
            {
                "totalResults": page.paginator.count,
                "itemsPerPage": page.paginator.per_page,
                "startIndex": page.start_index(),
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "Resources": [self.user_to_scim(connection) for connection in page],
            }
        )

    @atomic
    def update_user(self, connection: SCIMSourceUser | None, data: QueryDict):
        """Partial update a user"""
        properties = self.build_object_properties(data)

        if not properties.get("username"):
            raise ValidationError("Invalid user")

        user = connection.user if connection else User()
        if _user := User.objects.filter(username=properties.get("username")).first():
            user = _user
        user.update_attributes(properties)

        if not connection:
            connection, _ = SCIMSourceUser.objects.update_or_create(
                external_id=data.get("externalId") or str(uuid4()),
                source=self.source,
                user=user,
                defaults={
                    "attributes": data,
                },
            )
        else:
            connection.external_id = data.get("externalId", connection.external_id)
            connection.attributes = data
            connection.save()
        return connection

    def post(self, request: Request, **kwargs) -> Response:
        """Create user handler"""
        connection = SCIMSourceUser.objects.filter(
            Q(
                Q(user__uuid=request.data.get("id"))
                | Q(user__username=request.data.get("userName"))
            ),
            source=self.source,
        ).first()
        if connection:
            self.logger.debug("Found existing user")
            raise SCIMConflictError("Group with ID exists already.")
        connection = self.update_user(None, request.data)
        return Response(self.user_to_scim(connection), status=201)

    def patch(self, request: Request, user_id: str, **kwargs):
        connection = SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id).first()
        if not connection:
            raise SCIMNotFoundError("User not found.")
        patcher = SCIMPatchProcessor()
        patched_data = patcher.apply_patches(
            connection.attributes, request.data.get("Operations", [])
        )
        if patched_data != connection.attributes:
            self.update_user(connection, patched_data)
        return Response(self.user_to_scim(connection), status=200)

    def put(self, request: Request, user_id: str, **kwargs) -> Response:
        """Update user handler"""
        connection = SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id).first()
        if not connection:
            raise SCIMNotFoundError("User not found.")
        self.update_user(connection, request.data)
        return Response(self.user_to_scim(connection), status=200)

    @atomic
    def delete(self, request: Request, user_id: str, **kwargs) -> Response:
        """Delete user handler"""
        connection = SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id).first()
        if not connection:
            raise SCIMNotFoundError("User not found.")
        connection.user.delete()
        connection.delete()
        return Response(status=204)
