"""authentik core dataclasses"""
from dataclasses import dataclass
from typing import Optional

from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer


@dataclass
class UILoginButton:
    """Dataclass for Source's ui_login_button"""

    # Name, ran through i18n
    name: str

    # URL Which Button points to
    url: str

    # Icon URL, used as-is
    icon_url: Optional[str] = None


class UILoginButtonSerializer(PassiveSerializer):
    """Serializer for Login buttons of sources"""

    name = CharField()
    url = CharField()
    icon_url = CharField(required=False)


class UserSettingSerializer(PassiveSerializer):
    """Serializer for User settings for stages and sources"""

    object_uid = CharField()
    component = CharField()
    title = CharField()
