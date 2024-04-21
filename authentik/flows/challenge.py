"""Challenge helpers"""

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional, TypedDict
from uuid import UUID

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.http import JsonResponse
from rest_framework.fields import CharField, ChoiceField, DictField
from rest_framework.request import Request

from authentik.core.api.utils import PassiveSerializer
from authentik.lib.utils.errors import exception_to_string

if TYPE_CHECKING:
    from authentik.flows.stage import StageView

PLAN_CONTEXT_TITLE = "title"
PLAN_CONTEXT_URL = "url"
PLAN_CONTEXT_ATTRS = "attrs"


class FlowLayout(models.TextChoices):
    """Flow layouts"""

    STACKED = "stacked"
    CONTENT_LEFT = "content_left"
    CONTENT_RIGHT = "content_right"
    SIDEBAR_LEFT = "sidebar_left"
    SIDEBAR_RIGHT = "sidebar_right"


class ErrorDetailSerializer(PassiveSerializer):
    """Serializer for rest_framework's error messages"""

    string = CharField()
    code = CharField()


class ContextualFlowInfo(PassiveSerializer):
    """Contextual flow information for a challenge"""

    title = CharField(required=False, allow_blank=True)
    background = CharField(required=False)
    cancel_url = CharField()
    layout = ChoiceField(choices=[(x.value, x.name) for x in FlowLayout])


class DiscriminatorField(CharField):
    """Static field for use as discriminator for oneOf API endpoints"""

    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.required = True
        self.default = value
        self.fixed_value = value

    def to_representation(self):
        return self.fixed_value


class Challenge(PassiveSerializer):
    """Challenge that gets sent to the client based on which stage
    is currently active"""

    flow_info = ContextualFlowInfo(required=False)
    component = DiscriminatorField("")

    response_errors = DictField(
        child=ErrorDetailSerializer(many=True), allow_empty=True, required=False
    )


class RedirectChallenge(Challenge):
    """Challenge type to redirect the client"""

    to = CharField()
    component = DiscriminatorField("xak-flow-redirect")


class ShellChallenge(Challenge):
    """challenge type to render HTML as-is"""

    body = CharField()
    component = DiscriminatorField("xak-flow-shell")


class WithUserInfoMixin(PassiveSerializer):
    """Challenge base which shows some user info"""

    pending_user = CharField(allow_blank=True)
    pending_user_avatar = CharField()


class FlowErrorChallenge(Challenge):
    """Challenge class when an unhandled error occurs during a stage. Normal users
    are shown an error message, superusers are shown a full stacktrace."""

    component = DiscriminatorField("ak-stage-flow-error")

    request_id = CharField()

    error = CharField(required=False)
    traceback = CharField(required=False)

    def __init__(self, request: Request | None = None, error: Exception | None = None):
        super().__init__(data={})
        if not request or not error:
            return
        self.initial_data["request_id"] = request.request_id
        from authentik.core.models import USER_ATTRIBUTE_DEBUG

        if request.user and request.user.is_authenticated:
            if request.user.is_superuser or request.user.group_attributes(request).get(
                USER_ATTRIBUTE_DEBUG, False
            ):
                self.initial_data["error"] = str(error)
                self.initial_data["traceback"] = exception_to_string(error)


class AccessDeniedChallenge(WithUserInfoMixin, Challenge):
    """Challenge when a flow's active stage calls `stage_invalid()`."""

    error_message = CharField(required=False)
    component = DiscriminatorField("ak-stage-access-denied")


class PermissionDict(TypedDict):
    """Consent Permission"""

    id: str
    name: str


class ChallengeResponse(PassiveSerializer):
    """Base class for all challenge responses"""

    stage: Optional["StageView"]
    component = DiscriminatorField("xak-flow-response-default")

    def __init__(self, instance=None, data=None, **kwargs):
        self.stage = kwargs.pop("stage", None)
        super().__init__(instance=instance, data=data, **kwargs)


class AutosubmitChallenge(Challenge):
    """Autosubmit challenge used to send and navigate a POST request"""

    url = CharField()
    attrs = DictField(child=CharField(allow_blank=True), allow_empty=True)
    title = CharField(required=False)
    component = DiscriminatorField("ak-stage-autosubmit")


class AutoSubmitChallengeResponse(ChallengeResponse):
    """Pseudo class for autosubmit response"""

    component = DiscriminatorField("ak-stage-autosubmit")


class DataclassEncoder(DjangoJSONEncoder):
    """Convert any dataclass to json"""

    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, Enum):
            return o.value
        return super().default(o)  # pragma: no cover


class HttpChallengeResponse(JsonResponse):
    """Subclass of JsonResponse that uses the `DataclassEncoder`"""

    def __init__(self, challenge, **kwargs) -> None:
        super().__init__(challenge.data, encoder=DataclassEncoder, **kwargs)
