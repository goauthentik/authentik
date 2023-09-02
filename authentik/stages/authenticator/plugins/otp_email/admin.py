from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from .models import EmailDevice


class EmailDeviceAdmin(admin.ModelAdmin):
    """
    :class:`~django.contrib.admin.ModelAdmin` for
    :class:`~django_otp.plugins.otp_email.models.EmailDevice`.
    """

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
                "fields": ["email"],
            },
        ),
    ]
    raw_id_fields = ["user"]


# Somehow this is getting imported twice, triggering a useless exception.
try:
    admin.site.register(EmailDevice, EmailDeviceAdmin)
except AlreadyRegistered:
    pass
