"""authentik core dataclasses"""
from dataclasses import dataclass
from typing import Optional

from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.flows.challenge import Challenge


@dataclass(slots=True)
class UILoginButton:
    """Dataclass for Source's ui_login_button"""

    # Name, ran through i18n
    name: str

    # Challenge which is presented to the user when they click the button
    challenge: Challenge

    # Icon URL, used as-is
    icon_url: Optional[str] = None


class UserSettingSerializer(PassiveSerializer):
    """Serializer for User settings for stages and sources"""

    object_uid = CharField()
    component = CharField()
    title = CharField(required=True)
    configure_url = CharField(required=False)
    icon_url = CharField(required=False)
