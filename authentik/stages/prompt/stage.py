"""Prompt Stage Logic"""
from email.policy import Policy
from types import MethodType
from typing import Any, Callable, Iterator

from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_anonymous_user
from rest_framework.fields import BooleanField, CharField, ChoiceField, IntegerField, empty
from rest_framework.serializers import ValidationError

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.stage import ChallengeStageView
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyBindingModel, PolicyEngineMode
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.prompt.signals import password_validate

PLAN_CONTEXT_PROMPT = "prompt_data"


class StagePromptSerializer(PassiveSerializer):
    """Serializer for a single Prompt field"""

    field_key = CharField()
    label = CharField(allow_blank=True)
    type = ChoiceField(choices=FieldTypes.choices)
    required = BooleanField()
    placeholder = CharField(allow_blank=True)
    order = IntegerField()
    sub_text = CharField(allow_blank=True)


class PromptChallenge(Challenge):
    """Initial challenge being sent, define fields"""

    fields = StagePromptSerializer(many=True)
    component = CharField(default="ak-stage-prompt")


class PromptChallengeResponse(ChallengeResponse):
    """Validate response, fields are dynamically created based
    on the stage"""

    component = CharField(default="ak-stage-prompt")

    def __init__(self, *args, **kwargs):
        stage: PromptStage = kwargs.pop("stage", None)
        plan: FlowPlan = kwargs.pop("plan", None)
        request: HttpRequest = kwargs.pop("request", None)
        user: User = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.stage = stage
        self.plan = plan
        self.request = request
        if not self.stage:
            return
        # list() is called so we only load the fields once
        fields = list(self.stage.fields.all())
        for field in fields:
            field: Prompt
            current = field.get_placeholder(
                plan.context.get(PLAN_CONTEXT_PROMPT, {}), user, self.request
            )
            self.fields[field.field_key] = field.field(current)
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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # Check if we have any static or hidden fields, and ensure they
        # still have the same value
        static_hidden_fields: QuerySet[Prompt] = self.stage.fields.filter(
            type__in=[FieldTypes.HIDDEN, FieldTypes.STATIC, FieldTypes.TEXT_READ_ONLY]
        )
        for static_hidden in static_hidden_fields:
            field = self.fields[static_hidden.field_key]
            default = field.default
            # Prevent rest_framework.fields.empty from ending up in policies and events
            if default == empty:
                default = ""
            attrs[static_hidden.field_key] = default

        # Check if we have two password fields, and make sure they are the same
        password_fields: QuerySet[Prompt] = self.stage.fields.filter(type=FieldTypes.PASSWORD)
        if password_fields.exists() and password_fields.count() == 2:
            self._validate_password_fields(*[field.field_key for field in password_fields])

        user = self.plan.context.get(PLAN_CONTEXT_PENDING_USER, get_anonymous_user())
        engine = ListPolicyEngine(self.stage.validation_policies.all(), user, self.request)
        engine.mode = PolicyEngineMode.MODE_ALL
        engine.request.context[PLAN_CONTEXT_PROMPT] = attrs
        engine.use_cache = False
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
        password_validate.send(sender=self, password=value, plan_context=self.plan.context)
        return value

    return password_single_clean


class ListPolicyEngine(PolicyEngine):
    """Slightly modified policy engine, which uses a list instead of a PolicyBindingModel"""

    def __init__(self, policies: list[Policy], user: User, request: HttpRequest = None) -> None:
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

    response_class = PromptChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        fields: list[Prompt] = list(self.executor.current_stage.fields.all().order_by("order"))
        serializers = []
        context_prompt = self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {})
        for field in fields:
            data = StagePromptSerializer(field).data
            data["placeholder"] = field.get_placeholder(
                context_prompt, self.get_pending_user(), self.request
            )
            serializers.append(data)
        challenge = PromptChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "fields": serializers,
            },
        )
        return challenge

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        if not self.executor.plan:  # pragma: no cover
            raise ValueError
        return PromptChallengeResponse(
            instance=None,
            data=data,
            request=self.request,
            stage=self.executor.current_stage,
            plan=self.executor.plan,
            user=self.get_pending_user(),
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        if PLAN_CONTEXT_PROMPT not in self.executor.plan.context:
            self.executor.plan.context[PLAN_CONTEXT_PROMPT] = {}
        self.executor.plan.context[PLAN_CONTEXT_PROMPT].update(response.validated_data)
        return self.executor.stage_ok()
