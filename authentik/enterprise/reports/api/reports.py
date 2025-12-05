from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.core.models import User
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.reports.models import DataExport
from authentik.rbac.decorators import permission_required
from authentik.rbac.permissions import HasPermission
from authentik.enterprise.reports.tasks import generate_export


class RequestedBySerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("pk", "username")


class ContentTypeSerializer(ModelSerializer):
    app_label = CharField(read_only=True)
    model = CharField(read_only=True)

    class Meta:
        model = ContentType
        fields = ("id", "app_label", "model")


class DataExportSerializer(EnterpriseRequiredMixin, ModelSerializer):
    requested_by = RequestedBySerializer(read_only=True)
    content_type = ContentTypeSerializer(read_only=True)

    class Meta:
        model = DataExport
        fields = (
            "id",
            "requested_by",
            "requested_on",
            "content_type",
            "query_params",
            "file_url",
            "completed",
        )
        read_only_fields = (
            "id",
            "requested_by",
            "requested_on",
            "content_type",
            "file_url",
            "completed",
        )


class DataExportViewSet(
    mixins.RetrieveModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, GenericViewSet
):
    queryset = DataExport.objects.all()
    serializer_class = DataExportSerializer
    owner_field = "requested_by"
    ordering_fields = ["completed", "requested_by", "requested_on", "content_type__model"]
    ordering = ["-requested_on"]
    search_fields = ["requested_by__username", "content_type__model"]

    def get_queryset(self) -> QuerySet[DataExport]:
        """Limit to exports of content types the user has view permission on"""
        qs = super().get_queryset()
        permitted_cts = []
        for ct in ContentType.objects.filter(
            id__in=qs.values_list("content_type_id", flat=True).distinct()
        ):
            model = ct.model_class()
            if model is None:
                continue
            perm = f"{ct.app_label}.view_{ct.model}"
            if self.request.user.has_perm(perm):
                permitted_cts.append(ct)
        return qs.filter(content_type__in=permitted_cts)


class ExportMixin:
    @extend_schema(
        request=None,
        parameters=[],
        responses={201: DataExportSerializer},
        filters=True,
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[HasPermission("authentik_reports.add_dataexport")],
    )
    def export(self: GenericViewSet, request: Request) -> Response:
        """
        Create a data export for this data type. Note that the export is generated asynchronously:
        this method returns a `DataExport` object that will initially have `completed=false` as well
        as the permanent URL to that object in the `Location` header.
        You can poll that URL until `completed=true`, at which point the `file_url` property will
        contain a URL to download
        """

        s = DataExportSerializer(data={"query_params": request.query_params.dict()})
        s.is_valid(raise_exception=True)
        export = s.save(
            requested_by=request.user,
            content_type=ContentType.objects.get_for_model(self.queryset.model),
        )
        generate_export.send(export.id)

        set = export.serializer(instance=export)

        return Response(
            set.data,
            status=201,
            headers={"Location": reverse("authentik_api:dataexport-detail", args=[export.id])},
        )

    def get_permissions(self: GenericViewSet) -> list[BasePermission]:
        perms = super().get_permissions()
        if self.action == "export":
            model = self.get_queryset().model
            perms.append(HasPermission(f"{model._meta.app_label}.view_{model._meta.model_name}")())
        return perms
