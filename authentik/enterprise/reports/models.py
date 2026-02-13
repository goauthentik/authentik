import csv
import io
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.files.fields import FileField
from authentik.admin.files.manager import get_file_manager
from authentik.admin.files.usage import FileUsage
from authentik.core.models import User
from authentik.enterprise.reports.utils import MockRequest
from authentik.events.models import Event, EventAction, Notification, NotificationSeverity
from authentik.lib.models import SerializerModel
from authentik.lib.utils.db import chunked_queryset
from authentik.tenants.utils import get_current_tenant


class DataExport(SerializerModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    requested_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    requested_on = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    query_params = models.JSONField()
    file = FileField(blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Data Export")
        verbose_name_plural = _("Data Exports")

    @property
    def serializer(self) -> type[Serializer]:
        """Get serializer for this model"""
        from authentik.enterprise.reports.api.reports import DataExportSerializer

        return DataExportSerializer

    def generate(self) -> None:
        if self.completed:
            raise AssertionError("Data export must only be generated once")

        model_class = self.content_type.model_class()
        model_verbose_name = model_class._meta.verbose_name
        model_verbose_name_plural = model_class._meta.verbose_name_plural

        queryset = chunked_queryset(self.get_queryset())

        serializer = self.get_serializer_class()(
            context={"request": self._get_request()}, instance=queryset, many=True
        )
        self.file = f"{model_verbose_name_plural.lower()}_{self.id}.csv"

        with get_file_manager(FileUsage.REPORTS).save_file_stream(self.file) as f:
            with io.TextIOWrapper(f, encoding="utf-8", newline="") as text:
                writer = csv.writer(text)
                fields = [field.label for field in serializer.child.fields.values()]
                writer.writerow(fields)
                for record in queryset:
                    data = serializer.child.to_representation(record).values()
                    writer.writerow(data)
        self.completed = True
        self.save()

        message = _(f"{model_verbose_name} export generated successfully")
        e = Event.new(
            EventAction.EXPORT_READY,
            message=message,
            export=self,
        ).set_user(self.requested_by)
        e.save()
        Notification.objects.create(
            event=e,
            severity=NotificationSeverity.NOTICE,
            body=message,
            hyperlink=self.file_url,
            hyperlink_label=_("Download"),
            user=self.requested_by,
        )

    @property
    def file_url(self) -> str:
        return get_file_manager(FileUsage.REPORTS).file_url(self.file)

    def _get_request(self) -> MockRequest:
        return MockRequest(
            user=self.requested_by, query_params=self.query_params, tenant=get_current_tenant()
        )

    def get_queryset(self) -> models.QuerySet:
        request = self._get_request()
        viewset = self.get_viewset()
        viewset.request = request
        queryset = viewset.get_queryset()
        queryset = viewset.filter_queryset(queryset)

        return queryset

    def get_viewset(self) -> ModelViewSet:
        from authentik.core.api.users import UserViewSet
        from authentik.events.api.events import EventViewSet

        model = (self.content_type.app_label, self.content_type.model)
        if model == ("authentik_core", "user"):
            return UserViewSet()
        elif model == ("authentik_events", "event"):
            return EventViewSet()
        raise NotImplementedError(f"Unsupported data export type {self.content_type.model}")

    def get_serializer_class(self) -> type[Serializer]:
        from authentik.enterprise.reports.serializers import (
            ExportEventSerializer,
            ExportUserSerializer,
        )

        if self.content_type.model == "user":
            return ExportUserSerializer
        elif self.content_type.model == "event":
            return ExportEventSerializer
        return self.get_viewset().get_serializer_class()
