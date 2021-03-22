"""Challenge helpers"""
from enum import Enum
from typing import TYPE_CHECKING, Optional

from django.db.models.base import Model
from django.http import JsonResponse
from rest_framework.fields import ChoiceField, DictField
from rest_framework.serializers import CharField, Serializer

from authentik.flows.transfer.common import DataclassEncoder

if TYPE_CHECKING:
    from authentik.flows.stage import StageView


class ChallengeTypes(Enum):
    """Currently defined challenge types"""

    native = "native"
    shell = "shell"
    redirect = "redirect"


class ErrorDetailSerializer(Serializer):
    """Serializer for rest_framework's error messages"""

    string = CharField()
    code = CharField()

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()


class Challenge(Serializer):
    """Challenge that gets sent to the client based on which stage
    is currently active"""

    type = ChoiceField(
        choices=[(x.name, x.name) for x in ChallengeTypes],
    )
    component = CharField(required=False)
    title = CharField(required=False)
    background = CharField(required=False)

    response_errors = DictField(
        child=ErrorDetailSerializer(many=True), allow_empty=False, required=False
    )

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()


class RedirectChallenge(Challenge):
    """Challenge type to redirect the client"""

    to = CharField()


class ShellChallenge(Challenge):
    """Legacy challenge type to render HTML as-is"""

    body = CharField()


class WithUserInfoChallenge(Challenge):
    """Challenge base which shows some user info"""

    pending_user = CharField()
    pending_user_avatar = CharField()


class PermissionSerializer(Serializer):
    """Permission used for consent"""

    name = CharField()
    id = CharField()

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()


class ChallengeResponse(Serializer):
    """Base class for all challenge responses"""

    stage: Optional["StageView"]

    def __init__(self, instance=None, data=None, **kwargs):
        self.stage = kwargs.pop("stage", None)
        super().__init__(instance=instance, data=data, **kwargs)

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()


class HttpChallengeResponse(JsonResponse):
    """Subclass of JsonResponse that uses the `DataclassEncoder`"""

    def __init__(self, challenge, **kwargs) -> None:
        # pyright: reportGeneralTypeIssues=false
        super().__init__(challenge.data, encoder=DataclassEncoder, **kwargs)
