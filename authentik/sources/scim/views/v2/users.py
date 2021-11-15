"""SCIM User Views"""
from typing import Optional

from django.core.paginator import Paginator
from django.http import Http404, QueryDict
from django.urls import reverse
from guardian.shortcuts import get_anonymous_user
from rest_framework.request import Request
from rest_framework.response import Response
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.sources.scim.models import (
    USER_ATTRIBUTE_SCIM_ADDRESS,
    USER_ATTRIBUTE_SCIM_ENTERPRISE,
    USER_ATTRIBUTE_SCIM_ID,
)
from authentik.sources.scim.views.v2.base import SCIM_CONTENT_TYPE, SCIMView

LOGGER = get_logger()


class UsersView(SCIMView):
    """SCIM User view"""

    def get_email(self, data: list[dict]) -> str:
        """Wrapper to get primary email or first email"""
        for email in data:
            if email.get("primary", False):
                return email.get("value")
        return data[0].get("value")

    def user_to_scim(self, user: User) -> dict:
        """Convert User to SCIM data"""
        payload = {
            "id": str(user.pk),
            "meta": {
                "resourceType": "User",
                "created": user.date_joined,
                # TODO: use events to find last edit?
                "lastModified": user.date_joined,
                "location": self.request.build_absolute_uri(
                    reverse(
                        "authentik_sources_scim:v2-users",
                        kwargs={
                            "source_slug": self.kwargs["source_slug"],
                            "user_id": str(user.pk),
                        },
                    )
                ),
            },
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": user.attributes.get(
                USER_ATTRIBUTE_SCIM_ENTERPRISE, {}
            ),
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
            ],
            "userName": user.username,
            "name": {},
            "displayName": user.name,
            "active": user.is_active,
            "emails": [{"value": user.email, "type": "work", "primary": True}],
        }
        if USER_ATTRIBUTE_SCIM_ID in user.attributes:
            payload["externalId"] = user.attributes[USER_ATTRIBUTE_SCIM_ID]
        return payload

    def get(self, request: Request, user_id: Optional[str] = None, **kwargs) -> Response:
        """List User handler"""
        if user_id:
            user = User.objects.filter(pk=user_id).first()
            if not user:
                raise Http404
            return Response(self.user_to_scim(user))
        users = User.objects.all().exclude(pk=get_anonymous_user().pk).order_by("pk")
        per_page = 50
        paginator = Paginator(users, per_page=per_page)
        start_index = int(request.query_params.get("startIndex", 1))
        page = paginator.page(int(max(start_index / per_page, 1)))
        return Response(
            {
                "totalResults": paginator.count,
                "itemsPerPage": per_page,
                "startIndex": page.start_index(),
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "Resources": [self.user_to_scim(user) for user in page],
            }
        )

    def update_user(self, user: User, data: QueryDict) -> User:
        """Partial update a user"""
        if "userName" in data:
            user.username = data.get("userName")
        if "name" in data:
            user.name = data.get("name", {}).get("formatted", data.get("displayName"))
        if "emails" in data:
            user.email = self.get_email(data.get("emails"))
        if "active" in data:
            user.is_active = data.get("active")
        if "externalId" in data:
            user.attributes[USER_ATTRIBUTE_SCIM_ID] = data.get("externalId")
        if "addresses" in data:
            user.attributes[USER_ATTRIBUTE_SCIM_ADDRESS] = data.get("addresses")
        if "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User" in data:
            user.attributes[USER_ATTRIBUTE_SCIM_ENTERPRISE] = data.get(
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
            )
        return user

    def post(self, request: Request, **kwargs) -> Response:
        """Create user handler"""
        user = User.objects.filter(
            **{
                f"attributes__{USER_ATTRIBUTE_SCIM_ID}": request.data.get("externalId"),
                "username": request.data.get("userName"),
            }
        ).first()
        if user:
            LOGGER.debug("Found existing user")
            return Response(status=409)
        user = self.update_user(User(), request.data)
        user.save()
        return Response(self.user_to_scim(user), status=201)

    def patch(self, request: Request, user_id: str, **kwargs) -> Response:
        """Update user handler"""
        return self.put(request, user_id, **kwargs)

    def put(self, request: Request, user_id: str, **kwargs) -> Response:
        """Update user handler"""
        user: Optional[User] = User.objects.filter(pk=user_id).first()
        if not user:
            raise Http404
        self.update_user(user, request.data)
        user.save()
        return Response(self.user_to_scim(user), status=200)

    def delete(self, request: Request, user_id: str, **kwargs) -> Response:
        """Delete user handler"""
        user: Optional[User] = User.objects.filter(pk=user_id).first()
        if not user:
            raise Http404
        user.delete()
        return Response(
            {},
            status=204,
            headers={
                "Content-Type": SCIM_CONTENT_TYPE,
            },
        )
