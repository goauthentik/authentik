"""authentik core dataclasses"""
from dataclasses import dataclass
from typing import Optional

from rest_framework.fields import CharField, DictField

from authentik.core.api.utils import PassiveSerializer
from authentik.flows.challenge import Challenge


@dataclass
class UILoginButton:
    """Dataclass for Source's ui_login_button"""

    # Name, ran through i18n
    name: str

    # Challenge which is presented to the user when they click the button
    challenge: Challenge

    # Icon URL, used as-is
    icon_url: Optional[str] = None


class UILoginButtonSerializer(PassiveSerializer):
    """Serializer for Login buttons of sources"""

    name = CharField()
    challenge = DictField()
    icon_url = CharField(required=False, allow_null=True)


class UserSettingSerializer(PassiveSerializer):
    """Serializer for User settings for stages and sources"""

    object_uid = CharField()
    component = CharField()
    title = CharField()
    configure_url = CharField(required=False)
