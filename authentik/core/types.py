"""authentik core dataclasses"""
from dataclasses import dataclass
from typing import Optional

from django.db.models.base import Model
from rest_framework.fields import CharField
from rest_framework.serializers import Serializer


@dataclass
class UILoginButton:
    """Dataclass for Source's ui_login_button"""

    # Name, ran through i18n
    name: str

    # URL Which Button points to
    url: str

    # Icon URL, used as-is
    icon_url: Optional[str] = None


class UILoginButtonSerializer(Serializer):
    """Serializer for Login buttons of sources"""

    name = CharField()
    url = CharField()
    icon_url = CharField()

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()
