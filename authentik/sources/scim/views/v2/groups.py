"""SCIM Group Views"""

from uuid import uuid4

from django.db.models import Q
from django.db.transaction import atomic
from django.http import QueryDict
from django.urls import reverse
from pydantic import ValidationError as PydanticValidationError
from pydanticscim.group import GroupMember
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from scim2_filter_parser.attr_paths import AttrPath

from authentik.core.models import Group, User
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA, PatchOp, PatchOperation
from authentik.providers.scim.clients.schema import Group as SCIMGroupModel
from authentik.sources.scim.models import SCIMSourceGroup
from authentik.sources.scim.views.v2.base import SCIMObjectView
from authentik.sources.scim.views.v2.exceptions import (
    SCIMConflictError,
    SCIMNotFoundError,
    SCIMValidationError,
)


class GroupsView(SCIMObjectView):
    """SCIM Group view"""

    model = Group

    def group_to_scim(self, scim_group: SCIMSourceGroup) -> dict:
        """Convert Group to SCIM data"""
        payload = SCIMGroupModel(
            schemas=[SCIM_GROUP_SCHEMA],
            id=str(scim_group.group.pk),
            externalId=scim_group.id,
            displayName=scim_group.group.name,
            members=[],
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
        for member in scim_group.group.users.order_by("pk"):
            member: User
            payload.members.append(GroupMember(value=str(member.uuid)))
        return payload.model_dump(mode="json", exclude_unset=True)

    def get(self, request: Request, group_id: str | None = None, **kwargs) -> Response:
        """List Group handler"""
        base_query = SCIMSourceGroup.objects.select_related("group").prefetch_related(
            "group__users"
        )
        if group_id:
            connection = base_query.filter(source=self.source, group__group_uuid=group_id).first()
            if not connection:
                raise SCIMNotFoundError("Group not found.")
            return Response(self.group_to_scim(connection))
        connections = (
            base_query.filter(source=self.source).order_by("pk").filter(self.filter_parse(request))
        )
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
        properties = self.build_object_properties(data)

        if not properties.get("name"):
            raise ValidationError("Invalid group")

        group = connection.group if connection else Group()
        if _group := Group.objects.filter(name=properties.get("name")).first():
            group = _group

        group.update_attributes(properties)

        if "members" in data:
            query = Q()
            for _member in data.get("members", []):
                try:
                    member = GroupMember.model_validate(_member)
                except PydanticValidationError as exc:
                    self.logger.warning("Invalid group member", exc=exc)
                    continue
                query |= Q(uuid=member.value)
            if query:
                group.users.set(User.objects.filter(query))
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
            raise SCIMConflictError("Group with ID exists already.")
        connection = self.update_group(None, request.data)
        return Response(self.group_to_scim(connection), status=201)

    def put(self, request: Request, group_id: str, **kwargs) -> Response:
        """Update group handler"""
        connection = SCIMSourceGroup.objects.filter(
            source=self.source, group__group_uuid=group_id
        ).first()
        if not connection:
            raise SCIMNotFoundError("Group not found.")
        connection = self.update_group(connection, request.data)
        return Response(self.group_to_scim(connection), status=200)

    @atomic
    def patch(self, request: Request, group_id: str, **kwargs) -> Response:
        """Patch group handler"""
        connection = SCIMSourceGroup.objects.filter(
            source=self.source, group__group_uuid=group_id
        ).first()
        if not connection:
            raise SCIMNotFoundError("Group not found.")

        for _op in request.data.get("Operations", []):
            operation = PatchOperation.model_validate(_op)
            if operation.op.lower() not in ["add", "remove", "replace"]:
                raise SCIMValidationError()
            attr_path = AttrPath(f'{operation.path} eq ""', {})
            if attr_path.first_path == ("members", None, None):
                # FIXME: this can probably be de-duplicated
                if operation.op == PatchOp.add:
                    if not isinstance(operation.value, list):
                        operation.value = [operation.value]
                    query = Q()
                    for member in operation.value:
                        query |= Q(uuid=member["value"])
                    if query:
                        connection.group.users.add(*User.objects.filter(query))
                elif operation.op == PatchOp.remove:
                    if not isinstance(operation.value, list):
                        operation.value = [operation.value]
                    query = Q()
                    for member in operation.value:
                        query |= Q(uuid=member["value"])
                    if query:
                        connection.group.users.remove(*User.objects.filter(query))
        return Response(self.group_to_scim(connection), status=200)

    @atomic
    def delete(self, request: Request, group_id: str, **kwargs) -> Response:
        """Delete group handler"""
        connection = SCIMSourceGroup.objects.filter(
            source=self.source, group__group_uuid=group_id
        ).first()
        if not connection:
            raise SCIMNotFoundError("Group not found.")
        connection.group.delete()
        connection.delete()
        return Response(status=204)
