"""SCIM Group Views"""

from uuid import uuid4

from django.db.transaction import atomic
from django.http import Http404, QueryDict
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import Group
from authentik.providers.scim.clients.schema import Group as SCIMGroupModel
from authentik.sources.scim.models import SCIMSourceGroup
from authentik.sources.scim.views.v2.base import SCIMView


class GroupsView(SCIMView):
    """SCIM Group view"""

    model = Group

    def group_to_scim(self, scim_group: SCIMSourceGroup) -> dict:
        """Convert Group to SCIM data"""
        payload = SCIMGroupModel(
            id=str(scim_group.group.pk),
            externalId=scim_group.id,
            displayName=scim_group.group.name,
            meta={
                "resourceType": "Group",
                "location": self.request.build_absolute_uri(
                    reverse(
                        "authentik_sources_scim:v2-groups",
                        kwargs={
                            "source_slug": self.kwargs["source_slug"],
                            "group_id": str(scim_group.group.pk),
                        },
                    )
                ),
            },
        )
        return payload.model_dump(
            mode="json",
            exclude_unset=True,
        )

    def get(self, request: Request, group_id: str | None = None, **kwargs) -> Response:
        """List Group handler"""
        if group_id:
            connection = (
                SCIMSourceGroup.objects.filter(source=self.source, group__group_uuid=group_id)
                .select_related("group")
                .first()
            )
            if not connection:
                raise Http404
            return Response(self.group_to_scim(connection))
        connections = (
            SCIMSourceGroup.objects.filter(source=self.source)
            .select_related("group")
            .order_by("pk")
        )
        connections = connections.filter(self.filter_parse(request))
        page = self.paginate_query(connections)
        return Response(
            {
                "totalResults": page.paginator.count,
                "itemsPerPage": page.paginator.per_page,
                "startIndex": page.start_index(),
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "Resources": [self.group_to_scim(connection) for connection in page],
            }
        )

    @atomic
    def update_group(self, connection: SCIMSourceGroup | None, data: QueryDict):
        """Partial update a group"""
        group = connection.group if connection else Group()
        if "displayName" in data:
            group.name = data.get("displayName")
        if group.name == "":
            raise ValidationError("Invalid group")
        group.save()
        if not connection:
            connection, _ = SCIMSourceGroup.objects.get_or_create(
                source=self.source,
                group=group,
                attributes=data,
                id=data.get("externalId") or str(uuid4()),
            )
        else:
            connection.attributes = data
            connection.save()
        return connection

    def post(self, request: Request, **kwargs) -> Response:
        """Create group handler"""
        connection = SCIMSourceGroup.objects.filter(
            source=self.source,
            group__group_uuid=request.data.get("id"),
        ).first()
        if connection:
            self.logger.debug("Found existing group")
            return Response(status=409)
        connection = self.update_group(None, request.data)
        return Response(self.group_to_scim(connection), status=201)

    def put(self, request: Request, group_id: str, **kwargs) -> Response:
        """Update group handler"""
        connection = SCIMSourceGroup.objects.filter(
            source=self.source, group__group_uuid=group_id
        ).first()
        if not connection:
            raise Http404
        connection = self.update_group(connection, request.data)
        return Response(self.group_to_scim(connection), status=200)

    @atomic
    def delete(self, request: Request, group_id: str, **kwargs) -> Response:
        """Delete group handler"""
        connection = SCIMSourceGroup.objects.filter(
            source=self.source, group__group_uuid=group_id
        ).first()
        if not connection:
            raise Http404
        connection.group.delete()
        connection.delete()
        return Response(status=204)
