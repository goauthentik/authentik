"""Challenge helpers"""
from enum import Enum
from typing import TYPE_CHECKING, Optional

from django.db.models.base import Model
from django.http import JsonResponse
from rest_framework.fields import ChoiceField, JSONField
from rest_framework.serializers import CharField, Serializer

from authentik.flows.transfer.common import DataclassEncoder

if TYPE_CHECKING:
    from authentik.flows.stage import StageView


class ChallengeTypes(Enum):
    """Currently defined challenge types"""

    native = "native"
    shell = "shell"
    redirect = "redirect"
    error = "error"


class Challenge(Serializer):
    """Challenge that gets sent to the client based on which stage
    is currently active"""

    type = ChoiceField(choices=list(ChallengeTypes))
    component = CharField(required=False)
    args = JSONField()
    title = CharField(required=False)

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()


class ChallengeResponse(Serializer):
    """Base class for all challenge responses"""

    stage: Optional["StageView"]

    def __init__(self, instance, data, **kwargs):
        self.stage = kwargs.pop("stage", None)
        super().__init__(instance=instance, data=data, **kwargs)

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()


class HttpChallengeResponse(JsonResponse):
    """Subclass of JsonResponse that uses the `DataclassEncoder`"""

    def __init__(self, challenge: Challenge, **kwargs) -> None:
        # pyright: reportGeneralTypeIssues=false
        super().__init__(challenge.data, encoder=DataclassEncoder, **kwargs)
