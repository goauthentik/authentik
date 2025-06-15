"""SCIM User Views"""

from uuid import uuid4, UUID

from django.db.models import Q
from django.db.transaction import atomic
from django.http import Http404, QueryDict
from django.urls import reverse
from pydanticscim.user import Email, EmailKind, Name
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import User
from authentik.providers.scim.clients.schema import SCIM_USER_SCHEMA
from authentik.providers.scim.clients.schema import User as SCIMUserModel
from authentik.sources.scim.models import SCIMSourceUser
from authentik.sources.scim.views.v2.base import SCIMObjectView

class SCIMValidationError(APIException):
    status_code = 400
    default_detail = "Invalid syntax"
    default_code = "invalidSyntax"

    def __init__(self, detail=None, scim_type="invalidSyntax"):
        if detail is None:
            detail = self.default_detail
        self.detail = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "scimType": scim_type,
            "detail": detail,
        }

class UsersView(SCIMObjectView):
    """SCIM User view"""

    model = User

    def user_to_scim(self, scim_user: SCIMSourceUser) -> dict:
        """Convert User to SCIM data"""
        payload = SCIMUserModel(
            schemas=[SCIM_USER_SCHEMA],
            id=str(scim_user.user.uuid),
            externalId=scim_user.id,
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
                # TODO: use events to find last edit?
                "lastModified": scim_user.user.date_joined,
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
        return final_payload

    def get(self, request: Request, user_id: str | None = None, **kwargs) -> Response:
        """List User handler"""
        if user_id:
            try:
                UUID(user_id)
            except ValueError:
                raise Http404("User does not exist")
            connection = (
                SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id)
                .select_related("user")
                .first()
            )
            if not connection:
                raise Http404
            return Response(self.user_to_scim(connection))
        connections = (
            SCIMSourceUser.objects.filter(source=self.source).select_related("user").order_by("pk")
        )
        connections = connections.filter(self.filter_parse(request))
        page = self.paginate_query(connections)
        # Ensure startIndex matches the requested value (default 1)
        try:
            start_index = int(request.query_params.get("startIndex", 1))
            if start_index < 1:
                start_index = 1
        except (ValueError, TypeError):
            start_index = 1
        return Response(
            {
                "totalResults": page.paginator.count,
                "itemsPerPage": page.paginator.per_page,
                "startIndex": start_index,
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "Resources": [self.user_to_scim(connection) for connection in page],
            }
        )

    @atomic
    def update_user(self, connection: SCIMSourceUser | None, data: QueryDict):
        """Partial update a user"""
        properties = self.build_object_properties(data)

        if not properties.get("username"):
            raise SCIMValidationError("Missing required attribute: userName")

        user = connection.user if connection else User()
        if _user := User.objects.filter(username=properties.get("username")).first():
            user = _user
        user.update_attributes(properties)

        if not connection:
            connection, _ = SCIMSourceUser.objects.get_or_create(
                source=self.source,
                user=user,
                attributes=data,
                id=data.get("externalId") or str(uuid4()),
            )
        else:
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
            return Response(status=409)
        connection = self.update_user(None, request.data)
        return Response(self.user_to_scim(connection), status=201)

    def put(self, request: Request, user_id: str, **kwargs) -> Response:
        """Update user handler"""
        try:
            UUID(user_id)
        except ValueError:
            raise Http404("User does not exist")
        connection = SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id).first()
        if not connection:
            raise Http404
        self.update_user(connection, request.data)
        return Response(self.user_to_scim(connection), status=200)

    @atomic
    def patch(self, request: Request, user_id: str, **kwargs) -> Response:
        """Patch user handler"""
        try:
            UUID(user_id)
        except ValueError:
            raise Http404("User does not exist")
        connection = SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id).first()
        if not connection:
            raise Http404

        data = connection.attributes.copy() if hasattr(connection, "attributes") else {}
        operations = request.data.get("Operations", [])
        for op in operations:
            op_type = op.get("op", "").lower()
            path = op.get("path", "")
            value = op.get("value")

            if path.lower() == "username" or path.lower() == "userName":
                if op_type in ["replace", "add"]:
                    data["userName"] = value
                elif op_type == "remove":
                    data.pop("userName", None)
            # Add more SCIM attribute handling as needed

        connection = self.update_user(connection, data)
        return Response(self.user_to_scim(connection), status=200)

    @atomic
    def delete(self, request: Request, user_id: str, **kwargs) -> Response:
        """Delete user handler"""
        try:
            UUID(user_id)
        except ValueError:
            raise Http404("User does not exist")
        connection = SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id).first()
        if not connection:
            raise Http404
        connection.user.delete()
        connection.delete()
        return Response(status=204)
