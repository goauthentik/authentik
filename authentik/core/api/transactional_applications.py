"""transactional application and provider creation"""

from django.apps import apps
from django.db.models import Model
from django.utils.translation import gettext as _
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, extend_schema_field
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import BooleanField, CharField, ChoiceField, DictField, ListField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import ScalarNode

from authentik.blueprints.v1.common import (
    Blueprint,
    BlueprintEntry,
    BlueprintEntryDesiredState,
    EntryInvalidError,
    KeyOf,
)
from authentik.blueprints.v1.importer import Importer
from authentik.core.api.applications import ApplicationSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Application, Provider
from authentik.lib.utils.reflection import all_subclasses
from authentik.policies.api.bindings import PolicyBindingSerializer


def get_provider_serializer_mapping():
    """Get a mapping of all providers' model names and their serializers"""
    mapping = {}
    for model in all_subclasses(Provider):
        if model._meta.abstract:
            continue
        mapping[f"{model._meta.app_label}.{model._meta.model_name}"] = model().serializer
    return mapping


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="model",
        serializers=get_provider_serializer_mapping,
        resource_type_field_name="provider_model",
    )
)
class TransactionProviderField(DictField):
    """Dictionary field which can hold provider creation data"""


class TransactionPolicyBindingSerializer(PolicyBindingSerializer):
    """PolicyBindingSerializer which does not require target as target is set implicitly"""

    def validate(self, attrs):
        # As the PolicyBindingSerializer checks that the correct things can be bound to a target
        # but we don't have a target here as that's set by the blueprint, pass in an empty app
        # which will have the correct allowed combination of group/user/policy.
        attrs["target"] = Application()
        return super().validate(attrs)

    class Meta(PolicyBindingSerializer.Meta):
        fields = [x for x in PolicyBindingSerializer.Meta.fields if x != "target"]


class TransactionApplicationSerializer(PassiveSerializer):
    """Serializer for creating a provider and an application in one transaction"""

    app = ApplicationSerializer()
    provider_model = ChoiceField(choices=list(get_provider_serializer_mapping().keys()))
    provider = TransactionProviderField()

    policy_bindings = TransactionPolicyBindingSerializer(many=True, required=False)

    _provider_model: type[Provider] = None

    def validate_provider_model(self, fq_model_name: str) -> str:
        """Validate that the model exists and is a provider"""
        if "." not in fq_model_name:
            raise ValidationError("Invalid provider model")
        try:
            app, _, model_name = fq_model_name.partition(".")
            model = apps.get_model(app, model_name)
            if not issubclass(model, Provider):
                raise ValidationError("Invalid provider model")
            self._provider_model = model
        except LookupError:
            raise ValidationError("Invalid provider model") from None
        return fq_model_name

    def validate(self, attrs: dict) -> dict:
        blueprint = Blueprint()
        blueprint.entries.append(
            BlueprintEntry(
                model=attrs["provider_model"],
                state=BlueprintEntryDesiredState.MUST_CREATED,
                identifiers={
                    "name": attrs["provider"]["name"],
                },
                # Must match the name of the field on `self`
                id="provider",
                attrs=attrs["provider"],
            )
        )
        app_data = attrs["app"]
        app_data["provider"] = KeyOf(None, ScalarNode(tag="", value="provider"))
        blueprint.entries.append(
            BlueprintEntry(
                model="authentik_core.application",
                state=BlueprintEntryDesiredState.MUST_CREATED,
                identifiers={
                    "slug": attrs["app"]["slug"],
                },
                attrs=app_data,
                # Must match the name of the field on `self`
                id="app",
            )
        )
        for binding in attrs.get("policy_bindings", []):
            binding["target"] = KeyOf(None, ScalarNode(tag="", value="app"))
            for key, value in binding.items():
                if not isinstance(value, Model):
                    continue
                binding[key] = value.pk
            blueprint.entries.append(
                BlueprintEntry(
                    model="authentik_policies.policybinding",
                    state=BlueprintEntryDesiredState.MUST_CREATED,
                    identifiers=binding,
                )
            )
        importer = Importer(blueprint, {})
        try:
            valid, _ = importer.validate(raise_validation_errors=True)
            if not valid:
                raise ValidationError("Invalid blueprint")
        except EntryInvalidError as exc:
            raise ValidationError(
                {
                    exc.entry_id: exc.validation_error.detail,
                }
            ) from None
        return blueprint


class TransactionApplicationResponseSerializer(PassiveSerializer):
    """Transactional creation response"""

    applied = BooleanField()
    logs = ListField(child=CharField())


class TransactionalApplicationView(APIView):
    """Create provider and application and attach them in a single transaction"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TransactionApplicationSerializer(),
        responses={
            200: TransactionApplicationResponseSerializer(),
        },
    )
    def put(self, request: Request) -> Response:
        """Convert data into a blueprint, validate it and apply it"""
        data = TransactionApplicationSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        blueprint: Blueprint = data.validated_data
        for entry in blueprint.entries:
            full_model = entry.get_model(blueprint)
            app, __, model = full_model.partition(".")
            if not request.user.has_perm(f"{app}.add_{model}"):
                raise PermissionDenied(
                    {
                        entry.id: _(
                            "User lacks permission to create {model}".format_map(
                                {
                                    "model": full_model,
                                }
                            )
                        )
                    }
                )
        importer = Importer(blueprint, {})
        applied = importer.apply()
        response = {"applied": False, "logs": []}
        response["applied"] = applied
        return Response(response, status=200)
