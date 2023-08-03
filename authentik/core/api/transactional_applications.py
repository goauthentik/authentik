"""transactional application and provider creation"""
from django.apps import apps
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, ChoiceField, DictField, ListField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import ScalarNode

from authentik.blueprints.v1.common import (
    Blueprint,
    BlueprintEntry,
    BlueprintEntryDesiredState,
    KeyOf,
)
from authentik.blueprints.v1.importer import Importer
from authentik.core.api.applications import ApplicationSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Provider
from authentik.lib.utils.reflection import all_subclasses


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


class TransactionApplicationSerializer(PassiveSerializer):
    """Serializer for creating a provider and an application in one transaction"""

    app = ApplicationSerializer()
    provider_model = ChoiceField(choices=list(get_provider_serializer_mapping().keys()))
    provider = TransactionProviderField()

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
            raise ValidationError("Invalid provider model")
        return fq_model_name


class TransactionApplicationResponseSerializer(PassiveSerializer):
    """Transactional creation response"""

    valid = BooleanField()
    applied = BooleanField()
    logs = ListField(child=CharField())


class TransactionalApplicationView(APIView):
    """Create provider and application and attach them in a single transaction"""

    permission_classes = [IsAdminUser]

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
        print(data.validated_data)

        blueprint = Blueprint()
        blueprint.entries.append(
            BlueprintEntry(
                model=data.validated_data["provider_model"],
                state=BlueprintEntryDesiredState.MUST_CREATED,
                identifiers={
                    "name": data.validated_data["provider"]["name"],
                },
                id="provider",
                attrs=data.validated_data["provider"],
            )
        )
        app_data = data.validated_data["app"]
        app_data["provider"] = KeyOf(None, ScalarNode(tag="", value="provider"))
        blueprint.entries.append(
            BlueprintEntry(
                model="authentik_core.application",
                state=BlueprintEntryDesiredState.MUST_CREATED,
                identifiers={
                    "slug": data.validated_data["app"]["slug"],
                },
                attrs=app_data,
            )
        )
        importer = Importer(blueprint, {})
        response = {"valid": False, "applied": False, "logs": []}
        valid, logs = importer.validate()
        response["logs"] = [x["event"] for x in logs]
        response["valid"] = valid
        if valid:
            applied = importer.apply()
            response["applied"] = applied
        return Response(response, status=200)
