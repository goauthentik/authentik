"""SCIM User Views"""

from django.conf import settings
from django.core.paginator import Paginator
from django.db.transaction import atomic
from django.http import Http404, QueryDict
from pydanticscim.user import Email, EmailKind, Name
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import User
from authentik.providers.scim.clients.schema import User as SCIMUserModel
from authentik.sources.scim.models import SCIMSourceUser
from authentik.sources.scim.views.v2.base import SCIMView


class UsersView(SCIMView):
    """SCIM User view"""

    def get_email(self, data: list[dict]) -> str:
        """Wrapper to get primary email or first email"""
        for email in data:
            if email.get("primary", False):
                return email.get("value")
        return data[0].get("value")

    def user_to_scim(self, scim_user: SCIMSourceUser) -> dict:
        """Convert User to SCIM data"""
        payload = SCIMUserModel(
            id=str(scim_user.user.pk),
            externalId=scim_user.id,
            userName=scim_user.user.username,
            name=Name(
                formatted=scim_user.user.name,
            ),
            displayName=scim_user.user.name,
            active=scim_user.user.is_active,
            emails=[Email(value=scim_user.user.email, type=EmailKind.work, primary=True)],
        )
        # payload = {
        #     "meta": {
        #         "resourceType": "User",
        #         "created": scim_user.user.date_joined,
        #         # TODO: use events to find last edit?
        #         "lastModified": scim_user.user.date_joined,
        #         "location": self.request.build_absolute_uri(
        #             reverse(
        #                 "authentik_sources_scim:v2-users",
        #                 kwargs={
        #                     "source_slug": self.kwargs["source_slug"],
        #                     "user_id": str(scim_user.user.pk),
        #                 },
        #             )
        #         ),
        #     },
        # }
        return payload.model_dump(
            mode="json",
            exclude_unset=True,
        )

    def get(self, request: Request, user_id: str | None = None, **kwargs) -> Response:
        """List User handler"""
        if user_id:
            connection = (
                SCIMSourceUser.objects.filter(source=self.source, id=user_id)
                .select_related("user")
                .first()
            )
            if not connection:
                raise Http404
            return Response(self.user_to_scim(connection))
        connections = (
            SCIMSourceUser.objects.filter(source=self.source).select_related("user").order_by("pk")
        )
        per_page = settings.REST_FRAMEWORK["PAGE_SIZE"]
        paginator = Paginator(connections, per_page=per_page)
        start_index = int(request.query_params.get("startIndex", 1))
        page = paginator.page(int(max(start_index / per_page, 1)))
        return Response(
            {
                "totalResults": paginator.count,
                "itemsPerPage": per_page,
                "startIndex": page.start_index(),
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "Resources": [self.user_to_scim(connection) for connection in page],
            }
        )

    @atomic
    def update_user(self, connection: SCIMSourceUser | None, data: QueryDict):
        """Partial update a user"""
        user = connection.user if connection else User()
        if "userName" in data:
            user.username = data.get("userName")
        if "name" in data:
            user.name = data.get("name", {}).get("formatted", data.get("displayName"))
        if "emails" in data:
            user.email = self.get_email(data.get("emails"))
        if "active" in data:
            user.is_active = data.get("active")
        if user.username == "":
            raise ValidationError("Invalid user")
        user.save()
        if not connection:
            connection, _ = SCIMSourceUser.objects.get_or_create(
                source=self.source,
                user=user,
                attributes=data,
                id=data.get("externalId"),
            )
        else:
            connection.attributes = data
            connection.save()
        return connection

    def post(self, request: Request, **kwargs) -> Response:
        """Create user handler"""
        connection = SCIMSourceUser.objects.filter(
            source=self.source,
            id=request.data.get("externalId"),
        ).first()
        if connection:
            self.logger.debug("Found existing user")
            return Response(status=409)
        connection = self.update_user(None, request.data)
        return Response(self.user_to_scim(connection), status=201)

    def put(self, request: Request, user_id: str, **kwargs) -> Response:
        """Update user handler"""
        connection = SCIMSourceUser.objects.filter(source=self.source, id=user_id).first()
        if not connection:
            raise Http404
        self.update_user(connection, request.data)
        return Response(self.user_to_scim(connection), status=200)

    @atomic
    def delete(self, request: Request, user_id: str, **kwargs) -> Response:
        """Delete user handler"""
        connection = SCIMSourceUser.objects.filter(source=self.source, id=user_id).first()
        if not connection:
            raise Http404
        connection.user.delete()
        connection.delete()
        return Response({}, status=204)
