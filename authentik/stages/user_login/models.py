"""login stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.common.utils.time import timedelta_string_validator
from authentik.flows.models import Stage


class NetworkBinding(models.TextChoices):
    """Network session binding modes"""

    NO_BINDING = "no_binding"
    BIND_ASN = "bind_asn"  # Bind to ASN only
    BIND_ASN_NETWORK = "bind_asn_network"  # Bind to ASN and Network
    BIND_ASN_NETWORK_IP = "bind_asn_network_ip"  # Bind to ASN, Network and IP


class GeoIPBinding(models.TextChoices):
    """Geo session binding modes"""

    NO_BINDING = "no_binding"
    BIND_CONTINENT = "bind_continent"  # Bind to continent only
    BIND_CONTINENT_COUNTRY = "bind_continent_country"  # Bind to continent and country
    BIND_CONTINENT_COUNTRY_CITY = (
        "bind_continent_country_city"  # Bind to continent, country and city
    )


class UserLoginStage(Stage):
    """Attaches the currently pending user to the current session."""

    session_duration = models.TextField(
        default="seconds=0",
        validators=[timedelta_string_validator],
        help_text=_(
            "Determines how long a session lasts. Default of 0 means "
            "that the sessions lasts until the browser is closed. "
            "(Format: hours=-1;minutes=-2;seconds=-3)"
        ),
    )
    network_binding = models.TextField(
        choices=NetworkBinding.choices,
        default=NetworkBinding.NO_BINDING,
        help_text=_("Bind sessions created by this stage to the configured network"),
    )
    geoip_binding = models.TextField(
        choices=GeoIPBinding.choices,
        default=GeoIPBinding.NO_BINDING,
        help_text=_("Bind sessions created by this stage to the configured GeoIP location"),
    )
    terminate_other_sessions = models.BooleanField(
        default=False, help_text=_("Terminate all other sessions of the user logging in.")
    )
    remember_me_offset = models.TextField(
        default="seconds=0",
        validators=[timedelta_string_validator],
        help_text=_(
            "Offset the session will be extended by when the user picks the remember me option. "
            "Default of 0 means that the remember me option will not be shown. "
            "(Format: hours=-1;minutes=-2;seconds=-3)"
        ),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.user_login.api import UserLoginStageSerializer

        return UserLoginStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.user_login.stage import UserLoginStageView

        return UserLoginStageView

    @property
    def component(self) -> str:
        return "ak-stage-user-login-form"

    class Meta:
        verbose_name = _("User Login Stage")
        verbose_name_plural = _("User Login Stages")
