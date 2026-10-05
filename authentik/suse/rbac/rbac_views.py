from django.conf import settings
from guardian.models import RoleObjectPermission
from rest_framework.fields import CharField, IntegerField, SerializerMethodField

from authentik.api.pagination import Pagination
from authentik.core.api.utils import PassiveSerializer
from authentik.rbac.api.rbac_roles import RolePermissionViewSet as BaseRolePermissionViewSet


class SmartRoleObjectPermissionSerializer(PassiveSerializer):
    id = IntegerField(source="pk", read_only=True)

    app_label = CharField(source="content_type__app_label")
    app_label_verbose = CharField(source="content_type__app_label")
    model = CharField(source="content_type__model")
    model_verbose = CharField(source="content_type__model")
    object_description = SerializerMethodField()
    codename = CharField(source="permission__codename")
    name = SerializerMethodField()
    object_pk = CharField()

    def get_name(self, instance) -> str:
        app_label = instance["content_type__app_label"]
        codename = instance["permission__codename"]
        name = instance["permission__name"]

        return f"{name} ({app_label}.{codename})"

    def get_object_description(self, instance) -> str:
        model = instance["content_type__model"]
        object_pk = instance["object_pk"]

        return f"{model}#{object_pk}"


class RolePermissionViewSet(BaseRolePermissionViewSet):
    search_fields = [
        "permission__name",
        "permission__codename",
        "content_type__model",
        "content_type__app_label",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_suse_queryset_and_serializer = settings.OVERRIDE_ENDPOINT.get(
            "rbac_permissions_roles_list"
        )

    def get_serializer_class(self):
        if not self.use_suse_queryset_and_serializer:
            return super().get_serializer_class()
        return SmartRoleObjectPermissionSerializer

    @property
    def paginator(self):
        if not self.use_suse_queryset_and_serializer:
            return super().paginator

        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = Pagination()
        return self._paginator

    def get_queryset(self):
        if not self.use_suse_queryset_and_serializer:
            return super().get_queryset()

        required_fields = [
            "pk",
            "permission__name",
            "permission__codename",
            "content_type__app_label",
            "content_type__model",
            "object_pk",
        ]
        return RoleObjectPermission.objects.all().values(*required_fields)
