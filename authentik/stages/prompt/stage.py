"""Prompt Stage Logic"""
from email.policy import Policy
from types import MethodType
from typing import Any, Callable, Iterator

from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    IntegerField,
    ListField,
    empty,
)
from rest_framework.serializers import ValidationError

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import FlowPlan
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
    initial_value = CharField(allow_blank=True)
    order = IntegerField()
    sub_text = CharField(allow_blank=True)
    choices = ListField(child=CharField(allow_blank=True), allow_empty=True, allow_null=True)


class PromptChallenge(Challenge):
    """Initial challenge being sent, define fields"""

    fields = StagePromptSerializer(many=True)
    component = CharField(default="ak-stage-prompt")


class PromptChallengeResponse(ChallengeResponse):
    """Validate response, fields are dynamically created based
    on the stage"""

    stage_instance: PromptStage

    component = CharField(default="ak-stage-prompt")

    def __init__(self, *args, **kwargs):
        stage: PromptStage = kwargs.pop("stage_instance", None)
        plan: FlowPlan = kwargs.pop("plan", None)
        request: HttpRequest = kwargs.pop("request", None)
        user: User = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.stage_instance = stage
        self.plan = plan
        self.request = request
        if not self.stage_instance:
            return
        # list() is called so we only load the fields once
        fields = list(self.stage_instance.fields.all())
        for field in fields:
            field: Prompt
            choices = field.get_choices(
                plan.context.get(PLAN_CONTEXT_PROMPT, {}), user, self.request
            )
            current = field.get_initial_value(
                plan.context.get(PLAN_CONTEXT_PROMPT, {}), user, self.request
            )
            self.fields[field.field_key] = field.field(current, choices)
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
        static_hidden_fields: QuerySet[Prompt] = self.stage_instance.fields.filter(
            type__in=[
                FieldTypes.HIDDEN,
                FieldTypes.STATIC,
                FieldTypes.TEXT_READ_ONLY,
                FieldTypes.TEXT_AREA_READ_ONLY,
            ]
        )
        for static_hidden in static_hidden_fields:
            field = self.fields[static_hidden.field_key]
            default = field.default
            # Prevent rest_framework.fields.empty from ending up in policies and events
            if default == empty:
                default = ""
            attrs[static_hidden.field_key] = default

        # Check if we have two password fields, and make sure they are the same
        password_fields: QuerySet[Prompt] = self.stage_instance.fields.filter(
            type=FieldTypes.PASSWORD
        )
        if password_fields.exists() and password_fields.count() == 2:
            self._validate_password_fields(*[field.field_key for field in password_fields])

        engine = ListPolicyEngine(
            self.stage_instance.validation_policies.all(),
            self.stage.get_pending_user(),
            self.request,
        )
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

    def iterate_bindings(self) -> Iterator[PolicyBinding]:
        for policy in self.__list:
            yield PolicyBinding(
                policy=policy,
            )


class PromptStageView(ChallengeStageView):
    """Prompt Stage, save form data in plan context."""

    response_class = PromptChallengeResponse

    def get_prompt_challenge_fields(self, fields: list[Prompt], context: dict, dry_run=False):
        """Get serializers for all fields in `fields`, using the context `context`.
        If `dry_run` is set, property mapping expression errors are raised, otherwise they
        are logged and events are created"""
        serializers = []
        for field in fields:
            data = StagePromptSerializer(field).data
            # Ensure all choices, placeholders and initial values are str, as
            # otherwise further in we can fail serializer validation if we return
            # some types such as bool
            choices = field.get_choices(context, self.get_pending_user(), self.request, dry_run)
            if choices:
                data["choices"] = [str(choice) for choice in choices]
            else:
                data["choices"] = None
            data["placeholder"] = str(
                field.get_placeholder(context, self.get_pending_user(), self.request, dry_run)
            )
            data["initial_value"] = str(
                field.get_initial_value(context, self.get_pending_user(), self.request, dry_run)
            )
            serializers.append(data)
        return serializers

    def get_challenge(self, *args, **kwargs) -> Challenge:
        fields: list[Prompt] = list(self.executor.current_stage.fields.all().order_by("order"))
        context_prompt = self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {})
        serializers = self.get_prompt_challenge_fields(fields, context_prompt)
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
            stage_instance=self.executor.current_stage,
            stage=self,
            plan=self.executor.plan,
            user=self.get_pending_user(),
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        if PLAN_CONTEXT_PROMPT not in self.executor.plan.context:
            self.executor.plan.context[PLAN_CONTEXT_PROMPT] = {}
        self.executor.plan.context[PLAN_CONTEXT_PROMPT].update(response.validated_data)
        return self.executor.stage_ok()
