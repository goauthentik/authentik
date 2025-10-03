"Channels postgres app config"

from django.apps import AppConfig


class ChannelsPostgresConfig(AppConfig):
    """App Config."""

    name = "channels_postgres"
    default_auto_field = "django.db.models.AutoField"
