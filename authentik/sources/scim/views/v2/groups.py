"""SCIM Group Views"""

from uuid import uuid4, UUID

from django.db.models import Q
from django.db.transaction import atomic
from django.http import Http404, QueryDict
from django.urls import reverse
from pydantic import ValidationError as PydanticValidationError
from pydanticscim.group import GroupMember
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from authentik.providers.scim.clients.schema import SCIM_GROUP_SCHEMA
from authentik.core.models import Group, User
from authentik.providers.scim.clients.schema import SCIM_USER_SCHEMA
from authentik.providers.scim.clients.schema import Group as SCIMGroupModel
from authentik.sources.scim.models import SCIMSourceGroup
from authentik.sources.scim.views.v2.base import SCIMObjectView
from rest_framework.exceptions import APIException

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


class GroupsView(SCIMObjectView):
    """SCIM Group view"""
    model = Group

    def group_to_scim(self, scim_group: SCIMSourceGroup) -> dict:
        """Convert Group to SCIM data"""
        if not scim_group.group:
            raise Http404("Group does not exist")
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
            payload.members.append(GroupMember(value=str(member.uuid)))
        return payload.model_dump(mode="json", exclude_unset=True)

    def get(self, request: Request, group_id: str | None = None, **kwargs) -> Response:
        """List Group handler"""
        base_query = SCIMSourceGroup.objects.select_related("group").prefetch_related(
            "group__users"
        )
        if group_id:
            try:
                UUID(group_id)
            except ValueError:
                raise Http404("Group does not exist")
            connection = base_query.filter(source=self.source, group__group_uuid=group_id).first()
            if not connection or not connection.group:
                raise Http404("Group does not exist")
            return Response(self.group_to_scim(connection))
        connections = (
            base_query.filter(source=self.source).order_by("pk").filter(self.filter_parse(request))
        )
        page = self.paginate_query(connections)
        # Get startIndex from query params, default to 1 if not provided or invalid
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
                "Resources": [self.group_to_scim(connection) for connection in page if connection.group],
            }
        )

    @atomic
    def update_group(self, connection: SCIMSourceGroup | None, data: QueryDict):
        """Partial update a group"""
         # Ensure displayName is mapped to name for the model
        if "displayName" in data:
            data["name"] = data["displayName"]
        properties = self.build_object_properties(data)

        if not properties.get("name"):
            raise SCIMValidationError("Missing required attribute: displayName")

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
    def patch(self, request: Request, group_id: str, **kwargs) -> Response:
        """Patch group handler"""
        connection = SCIMSourceGroup.objects.filter(
            source=self.source, group__group_uuid=group_id
        ).first()
        if not connection:
            raise Http404

        data = connection.attributes.copy() if hasattr(connection, "attributes") else {}
        current_members = {m.get("value") for m in data.get("members", []) if m.get("value")}

        operations = request.data.get("Operations", [])
        for op in operations:
            op_type = op.get("op", "").lower()
            path = op.get("path", "")
            value = op.get("value")

            if path.lower() == "displayname":
                if op_type in ["replace", "add"]:
                    data["displayName"] = value
                    data["name"] = value  # Ensure both are set for your internal logic
                elif op_type == "remove":
                    data.pop("displayName", None)
                    data.pop("name", None)

            elif path.lower() == "members":
                if op_type == "replace":
                    # Replace all members
                    data["members"] = value if value is not None else []
                    current_members = {m.get("value") for m in data["members"] if m.get("value")}
                elif op_type == "add":
                    # Add only new members
                    if not isinstance(value, list):
                        value = [value]
                    for member in value:
                        member_id = member.get("value")
                        if member_id and member_id not in current_members:
                            data.setdefault("members", []).append(member)
                            current_members.add(member_id)
                elif op_type == "remove":
                    if value is None:
                        # Remove all members
                        data["members"] = []
                        current_members = set()
                    else:
                        if not isinstance(value, list):
                            value = [value]
                        remove_ids = {m.get("value") for m in value if m.get("value")}
                        data["members"] = [m for m in data.get("members", []) if m.get("value") not in remove_ids]
                        current_members -= remove_ids

        connection = self.update_group(connection, data)
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
