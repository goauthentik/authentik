"""Prompt Stage Logic"""
from email.policy import Policy
from types import MethodType
from typing import Any, Callable, Iterator

from django.db.models.base import Model
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_anonymous_user
from rest_framework.fields import BooleanField, CharField, IntegerField
from rest_framework.serializers import Serializer, ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.stage import ChallengeStageView
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyBindingModel
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.prompt.signals import password_validate

LOGGER = get_logger()
PLAN_CONTEXT_PROMPT = "prompt_data"


class PromptSerializer(Serializer):
    """Serializer for a single Prompt field"""

    field_key = CharField()
    label = CharField()
    type = CharField()
    required = BooleanField()
    placeholder = CharField()
    order = IntegerField()

    def create(self, validated_data: dict) -> Model:
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:
        return Model()


class PromptChallenge(Challenge):
    """Initial challenge being sent, define fields"""

    fields = PromptSerializer(many=True)


class PromptResponseChallenge(ChallengeResponse):
    """Validate response, fields are dynamically created based
    on the stage"""

    def __init__(self, *args, stage: PromptStage, plan: FlowPlan, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage = stage
        self.plan = plan
        # list() is called so we only load the fields once
        fields = list(self.stage.fields.all())
        for field in fields:
            field: Prompt
            self.fields[field.field_key] = field.field
            # Special handling for fields with username type
            # these check for existing users with the same username
            if field.type == FieldTypes.USERNAME:
                setattr(
                    self,
                    f"validate_{field.field_key}",
                    MethodType(username_field_validator_factory(), self),
                )
            # Check if we have a password field, add a handler that sends a signal
            # to validate it
            if field.type == FieldTypes.PASSWORD:
                setattr(
                    self,
                    f"validate_{field.field_key}",
                    MethodType(password_single_validator_factory(), self),
                )

        self.field_order = sorted(fields, key=lambda x: x.order)

    def _validate_password_fields(self, *field_names):
        """Check if the value of all password fields match by merging them into a set
        and checking the length"""
        all_passwords = {self.initial_data[x] for x in field_names}
        if len(all_passwords) > 1:
            raise ValidationError(_("Passwords don't match."))

    def validate(self, attrs):
        if attrs == {}:
            return {}
        # Check if we have two password fields, and make sure they are the same
        password_fields: QuerySet[Prompt] = self.stage.fields.filter(
            type=FieldTypes.PASSWORD
        )
        if password_fields.exists() and password_fields.count() == 2:
            self._validate_password_fields(
                *[field.field_key for field in password_fields]
            )

        user = self.plan.context.get(PLAN_CONTEXT_PENDING_USER, get_anonymous_user())
        engine = ListPolicyEngine(self.stage.validation_policies.all(), user)
        engine.request.context = attrs
        engine.build()
        result = engine.result
        if not result.passing:
            raise ValidationError(list(result.messages))
        return attrs


def username_field_validator_factory() -> Callable[[PromptChallenge, str], Any]:
    """Return a `clean_` method for `field`. Clean method checks if username is taken already."""

    # pylint: disable=unused-argument
    def username_field_validator(self: PromptChallenge, value: str) -> Any:
        """Check for duplicate usernames"""
        if User.objects.filter(username=value).exists():
            raise ValidationError("Username is already taken.")
        return value

    return username_field_validator


def password_single_validator_factory() -> Callable[[PromptChallenge, str], Any]:
    """Return a `clean_` method for `field`. Clean method checks if username is taken already."""

    def password_single_clean(self: PromptChallenge, value: str) -> Any:
        """Send password validation signals for e.g. LDAP Source"""
        password_validate.send(
            sender=self, password=value, plan_context=self.plan.context
        )
        return value

    return password_single_clean


class ListPolicyEngine(PolicyEngine):
    """Slightly modified policy engine, which uses a list instead of a PolicyBindingModel"""

    __list: list[Policy]

    def __init__(
        self, policies: list[Policy], user: User, request: HttpRequest = None
    ) -> None:
        super().__init__(PolicyBindingModel(), user, request)
        self.__list = policies
        self.use_cache = False

    def _iter_bindings(self) -> Iterator[PolicyBinding]:
        for policy in self.__list:
            yield PolicyBinding(
                policy=policy,
            )


class PromptStageView(ChallengeStageView):
    """Prompt Stage, save form data in plan context."""

    response_class = PromptResponseChallenge

    def get_challenge(self, *args, **kwargs) -> Challenge:
        fields = list(self.executor.current_stage.fields.all().order_by("order"))
        challenge = PromptChallenge(
            data={
                "type": ChallengeTypes.native.value,
                "component": "ak-stage-prompt",
                "fields": [PromptSerializer(field).data for field in fields],
            },
        )
        return challenge

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        if not self.executor.plan:
            raise ValueError
        return PromptResponseChallenge(
            instance=None,
            data=data,
            stage=self.executor.current_stage,
            plan=self.executor.plan,
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        if PLAN_CONTEXT_PROMPT not in self.executor.plan.context:
            self.executor.plan.context[PLAN_CONTEXT_PROMPT] = {}
        self.executor.plan.context[PLAN_CONTEXT_PROMPT].update(response.validated_data)
        return self.executor.stage_ok()
