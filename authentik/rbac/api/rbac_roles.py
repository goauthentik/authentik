"""common RBAC serializers"""
from typing import Optional

from django.apps import apps
from django_filters.filters import UUIDFilter
from django_filters.filterset import FilterSet
from guardian.models import GroupObjectPermission
from guardian.shortcuts import get_objects_for_group
from rest_framework.fields import SerializerMethodField
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from authentik.api.pagination import SmallerPagination
from authentik.rbac.api.rbac_assigned_by_roles import RoleObjectPermissionSerializer


class ExtraRoleObjectPermissionSerializer(RoleObjectPermissionSerializer):
    """User permission with additional object-related data"""

    app_label_verbose = SerializerMethodField()
    model_verbose = SerializerMethodField()

    object_description = SerializerMethodField()

    def get_app_label_verbose(self, instance: GroupObjectPermission) -> str:
        """Get app label from permission's model"""
        return apps.get_app_config(instance.content_type.app_label).verbose_name

    def get_model_verbose(self, instance: GroupObjectPermission) -> str:
        """Get model label from permission's model"""
        return apps.get_model(
            instance.content_type.app_label, instance.content_type.model
        )._meta.verbose_name

    def get_object_description(self, instance: GroupObjectPermission) -> Optional[str]:
        """Get model description from attached model. This operation takes at least
        one additional query, and the description is only shown if the user/role has the
        view_ permission on the object"""
        app_label = instance.content_type.app_label
        model = instance.content_type.model
        model_class = apps.get_model(app_label, model)
        objects = get_objects_for_group(instance.group, f"{app_label}.view_{model}", model_class)
        obj = objects.first()
        if not obj:
            return None
        return str(obj)

    class Meta(RoleObjectPermissionSerializer.Meta):
        fields = RoleObjectPermissionSerializer.Meta.fields + [
            "app_label_verbose",
            "model_verbose",
            "object_description",
        ]


class RolePermissionFilter(FilterSet):
    """Role permission filter"""

    uuid = UUIDFilter("group__role__uuid", required=True)


class RolePermissionViewSet(ListModelMixin, GenericViewSet):
    """Get a role's assigned object permissions"""

    serializer_class = ExtraRoleObjectPermissionSerializer
    ordering = ["group__role__name"]
    pagination_class = SmallerPagination
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = GroupObjectPermission.objects.select_related("content_type", "group__role").all()
    filterset_class = RolePermissionFilter
