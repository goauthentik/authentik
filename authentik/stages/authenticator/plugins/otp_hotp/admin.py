from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from authentik.stages.authenticator.conf import settings

from .models import HOTPDevice


class HOTPDeviceAdmin(admin.ModelAdmin):
    """
    :class:`~django.contrib.admin.ModelAdmin` for
    :class:`~django_otp.plugins.otp_hotp.models.HOTPDevice`.
    """

    list_display = ["user", "name", "confirmed"]

    raw_id_fields = ["user"]
    readonly_fields = ["qrcode_link"]
    radio_fields = {"digits": admin.HORIZONTAL}

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if not settings.OTP_ADMIN_HIDE_SENSITIVE_DATA:
            list_display = [*list_display, "qrcode_link"]
        return list_display

    def get_fieldsets(self, request, obj=None):
        # Show the key value only for adding new objects or when sensitive data
        # is not hidden.
        if settings.OTP_ADMIN_HIDE_SENSITIVE_DATA and obj:
            configuration_fields = ["digits", "tolerance"]
        else:
            configuration_fields = ["key", "digits", "tolerance"]
        fieldsets = [
            (
                "Identity",
                {
                    "fields": ["user", "name", "confirmed"],
                },
            ),
            (
                "Configuration",
                {
                    "fields": configuration_fields,
                },
            ),
            (
                "State",
                {
                    "fields": ["counter"],
                },
            ),
            (
                "Throttling",
                {
                    "fields": [
                        "throttling_failure_timestamp",
                        "throttling_failure_count",
                    ],
                },
            ),
        ]
        # Show the QR code link only for existing objects when sensitive data
        # is not hidden.
        if not settings.OTP_ADMIN_HIDE_SENSITIVE_DATA and obj:
            fieldsets.append(
                (
                    None,
                    {
                        "fields": ["qrcode_link"],
                    },
                ),
            )
        return fieldsets

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("user")

        return queryset

    #
    # Columns
    #

    def qrcode_link(self, device):
        try:
            href = reverse("admin:otp_hotp_hotpdevice_config", kwargs={"pk": device.pk})
            link = format_html('<a href="{}">qrcode</a>', href)
        except Exception:
            link = ""

        return link

    qrcode_link.short_description = "QR Code"

    #
    # Custom views
    #

    def get_urls(self):
        urls = [
            path(
                "<int:pk>/config/",
                self.admin_site.admin_view(self.config_view),
                name="otp_hotp_hotpdevice_config",
            ),
            path(
                "<int:pk>/qrcode/",
                self.admin_site.admin_view(self.qrcode_view),
                name="otp_hotp_hotpdevice_qrcode",
            ),
        ] + super().get_urls()

        return urls

    def config_view(self, request, pk):
        if settings.OTP_ADMIN_HIDE_SENSITIVE_DATA:
            raise PermissionDenied()

        device = HOTPDevice.objects.get(pk=pk)
        if not self.has_view_or_change_permission(request, device):
            raise PermissionDenied()

        context = dict(
            self.admin_site.each_context(request),
            device=device,
        )

        return TemplateResponse(request, "otp_hotp/admin/config.html", context)

    def qrcode_view(self, request, pk):
        if settings.OTP_ADMIN_HIDE_SENSITIVE_DATA:
            raise PermissionDenied()

        device = HOTPDevice.objects.get(pk=pk)
        if not self.has_view_or_change_permission(request, device):
            raise PermissionDenied()

        try:
            import qrcode
            import qrcode.image.svg

            img = qrcode.make(device.config_url, image_factory=qrcode.image.svg.SvgImage)
            response = HttpResponse(content_type="image/svg+xml")
            img.save(response)
        except ImportError:
            response = HttpResponse("", status=503)

        return response


try:
    admin.site.register(HOTPDevice, HOTPDeviceAdmin)
except AlreadyRegistered:
    # A useless exception from a double import
    pass
