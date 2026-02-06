"""authentik core dataclasses"""

from dataclasses import dataclass

from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer, ThemedUrlsSerializer
from authentik.flows.challenge import Challenge


@dataclass(slots=True)
class UILoginButton:
    """Dataclass for Source's ui_login_button"""

    # Name, ran through i18n
    name: str

    # Challenge which is presented to the user when they click the button
    challenge: Challenge

    # Icon URL, used as-is
    icon_url: str | None = None

    # Pre-resolved themed icon URLs for light/dark variants
    icon_themed_urls: dict[str, str] | None = None

    # Whether this source should be displayed as a prominent button
    promoted: bool = False


class UserSettingSerializer(PassiveSerializer):
    """Serializer for User settings for stages and sources"""

    object_uid = CharField()
    component = CharField()
    title = CharField(required=True)
    configure_url = CharField(required=False)
    icon_url = CharField(required=False, allow_null=True)
    icon_themed_urls = ThemedUrlsSerializer(required=False, allow_null=True)
