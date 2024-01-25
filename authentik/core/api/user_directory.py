"""User directory API Views"""
from typing import Any

from drf_spectacular.utils import extend_schema, inline_serializer
from guardian.shortcuts import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import CharField, DictField, ListField, ModelSerializer
from rest_framework.views import Request, Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.rbac.permissions import HasPermission
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


class UserDirectorySerializer(ModelSerializer):
    """User Directory Serializer"""

    user_fields = SerializerMethodField()
    attributes = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "pk",
            "user_fields",
            "attributes",
        ]

    def get_user_fields(self, obj: User) -> dict[str, Any]:
        """Get directory fields"""
        fields = {}
        user_directory_fields = get_current_tenant().user_directory_fields
        for f in ("name", "username", "email", "avatar"):
            if f in user_directory_fields:
                fields[f] = getattr(obj, f)
        if "groups" in user_directory_fields:
            fields["groups"] = [g.name for g in obj.all_groups().order_by("name")]
        return fields

    def get_attributes(self, obj: User) -> dict[str, Any]:
        """Get directory attributes"""
        attributes = {}
        for field in get_current_tenant().user_directory_attributes:
            path = field.get("attribute", None)
            if path is not None:
                attributes[path] = obj.attributes.get(path, None)
        return attributes


class UserDirectoryViewSet(ReadOnlyModelViewSet):
    """User Directory Viewset"""

    queryset = User.objects.none()
    ordering = ["username"]
    ordering_fields = ["username", "email", "name"]
    serializer_class = UserDirectorySerializer
    permission_classes = [HasPermission("authentik_rbac.view_user_directory")]

    def get_queryset(self):
        return User.objects.all().exclude(pk=get_anonymous_user().pk).filter(is_active=True)

    @property
    def search_fields(self):
        """Get search fields"""
        current_tenant = get_current_tenant()
        return list(
            f for f in current_tenant.user_directory_fields if f not in ("avatar", "groups")
        ) + list(
            f"attributes__{attr['attribute']}"
            for attr in current_tenant.user_directory_attributes
            if "attribute" in attr
        )

    @extend_schema(
        responses={
            200: inline_serializer(
                "UserDirectoryFieldsSerializer",
                {
                    "fields": ListField(child=CharField()),
                    "attributes": ListField(child=DictField(child=CharField())),
                },
            )
        },
    )
    @action(detail=False, pagination_class=None)
    def fields(self, request: Request) -> Response:
        """Get user directory fields"""
        return Response(
            {
                "fields": request.tenant.user_directory_fields,
                "attributes": request.tenant.user_directory_attributes,
            }
        )
