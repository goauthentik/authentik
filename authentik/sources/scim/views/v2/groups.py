"""SCIM Group Views"""
from typing import Optional

from django.core.paginator import Paginator
from django.http import Http404, QueryDict
from django.urls import reverse
from rest_framework.request import Request
from rest_framework.response import Response
from structlog.stdlib import get_logger

from authentik.core.models import Group
from authentik.sources.scim.views.v2.base import SCIM_CONTENT_TYPE, SCIMView

LOGGER = get_logger()


class GroupsView(SCIMView):
    """SCIM Group View"""

    def group_to_scim(self, group: Group) -> dict:
        """Convert group to SCIM"""
        return {
            "id": str(group.pk),
            "meta": {
                "resourceType": "Group",
                "location": self.request.build_absolute_uri(
                    reverse(
                        "authentik_sources_scim:v2-groups",
                        kwargs={
                            "source_slug": self.kwargs["source_slug"],
                            "group_id": str(group.pk),
                        },
                    )
                ),
            },
            "displayName": group.name,
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        }

    def get(self, request: Request, group_id: Optional[str] = None, **kwargs) -> Response:
        """List Group handler"""
        if group_id:
            group = Group.objects.filter(pk=group_id).first()
            if not group:
                raise Http404
            return Response(self.group_to_scim(group))
        groups = Group.objects.all().order_by("pk")
        per_page = 50
        paginator = Paginator(groups, per_page=per_page)
        start_index = int(request.query_params.get("startIndex", 1))
        page = paginator.page(int(max(start_index / per_page, 1)))
        return Response(
            {
                "totalResults": paginator.count,
                "itemsPerPage": per_page,
                "startIndex": page.start_index(),
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "Resources": [self.group_to_scim(group) for group in page],
            }
        )

    def update_group(self, group: Group, data: QueryDict) -> Group:
        """Partial update a group"""
        if "displayName" in data:
            group.name = data.get("displayName")
        return group

    def post(self, request: Request, **kwargs) -> Response:
        """Create group handler"""
        group = Group.objects.filter(name=request.data.get("displayName")).first()
        if group:
            LOGGER.debug("Found existing group")
            return Response(status=409)
        group = self.update_group(Group(), request.data)
        group.save()
        return Response(self.group_to_scim(group), status=201)

    def patch(self, request: Request, group_id: str, **kwargs) -> Response:
        """Update group handler"""
        return self.put(request, group_id, **kwargs)

    def put(self, request: Request, group_id: str, **kwargs) -> Response:
        """Update group handler"""
        group: Optional[Group] = Group.objects.filter(pk=group_id).first()
        if not group:
            raise Http404
        self.update_group(group, request.data)
        group.save()
        return Response(self.group_to_scim(group), status=200)

    def delete(self, request: Request, group_id: str, **kwargs) -> Response:
        """Delete group handler"""
        group: Optional[Group] = Group.objects.filter(pk=group_id).first()
        if not group:
            raise Http404
        group.delete()
        return Response(
            {},
            status=204,
            headers={
                "Content-Type": SCIM_CONTENT_TYPE,
            },
        )
