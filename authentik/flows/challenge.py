"""Challenge helpers"""
from enum import Enum
from typing import TYPE_CHECKING, Optional

from django.http import JsonResponse
from rest_framework.fields import ChoiceField, DictField
from rest_framework.serializers import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.flows.transfer.common import DataclassEncoder

if TYPE_CHECKING:
    from authentik.flows.stage import StageView


class ChallengeTypes(Enum):
    """Currently defined challenge types"""

    NATIVE = "native"
    SHELL = "shell"
    REDIRECT = "redirect"


class ErrorDetailSerializer(PassiveSerializer):
    """Serializer for rest_framework's error messages"""

    string = CharField()
    code = CharField()


class Challenge(PassiveSerializer):
    """Challenge that gets sent to the client based on which stage
    is currently active"""

    type = ChoiceField(
        choices=[(x.value, x.name) for x in ChallengeTypes],
    )
    title = CharField(required=False)
    background = CharField(required=False)
    component = CharField(default="")

    response_errors = DictField(
        child=ErrorDetailSerializer(many=True), allow_empty=True, required=False
    )


class RedirectChallenge(Challenge):
    """Challenge type to redirect the client"""

    to = CharField()
    component = CharField(default="xak-flow-redirect")


class ShellChallenge(Challenge):
    """challenge type to render HTML as-is"""

    body = CharField()
    component = CharField(default="xak-flow-shell")


class WithUserInfoChallenge(Challenge):
    """Challenge base which shows some user info"""

    pending_user = CharField()
    pending_user_avatar = CharField()


class AccessDeniedChallenge(Challenge):
    """Challenge when a flow's active stage calls `stage_invalid()`."""

    error_message = CharField(required=False)
    component = CharField(default="ak-stage-access-denied")


class PermissionSerializer(PassiveSerializer):
    """Permission used for consent"""

    name = CharField()
    id = CharField()


class ChallengeResponse(PassiveSerializer):
    """Base class for all challenge responses"""

    stage: Optional["StageView"]
    component = CharField(default="xak-flow-response-default")

    def __init__(self, instance=None, data=None, **kwargs):
        self.stage = kwargs.pop("stage", None)
        super().__init__(instance=instance, data=data, **kwargs)


class HttpChallengeResponse(JsonResponse):
    """Subclass of JsonResponse that uses the `DataclassEncoder`"""

    def __init__(self, challenge, **kwargs) -> None:
        # pyright: reportGeneralTypeIssues=false
        super().__init__(challenge.data, encoder=DataclassEncoder, **kwargs)
