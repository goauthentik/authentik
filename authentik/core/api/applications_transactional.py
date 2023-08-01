from django.apps import apps
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ChoiceField, DictField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import ScalarNode
from authentik.blueprints.v1.common import Blueprint, BlueprintEntry, BlueprintEntryDesiredState, KeyOf
from authentik.blueprints.v1.importer import Importer

from authentik.core.api.applications import ApplicationSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Provider
from authentik.lib.utils.reflection import all_subclasses


def get_provider_serializer_mapping():
    map = {}
    for model in all_subclasses(Provider):
        if model._meta.abstract:
            continue
        map[f"{model._meta.app_label}.{model._meta.model_name}"] = model().serializer
    return map


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="model",
        serializers=get_provider_serializer_mapping,
        resource_type_field_name="provider_model",
    )
)
class TransactionProviderField(DictField):
    pass


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
            app, model_name = fq_model_name.split(".")
            model = apps.get_model(app, model_name)
            if not issubclass(model, Provider):
                raise ValidationError("Invalid provider model")
            self._provider_model = model
        except LookupError:
            raise ValidationError("Invalid provider model")
        return fq_model_name

    def validate_provider(self, provider: dict) -> dict:
        """Validate provider data"""
        # ensure the model has been validated
        self.validate_provider_model(self.initial_data["provider_model"])
        model_serializer = self._provider_model().serializer(data=provider)
        model_serializer.is_valid(raise_exception=True)
        return model_serializer.validated_data


class TransactionalApplicationView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=TransactionApplicationSerializer())
    def put(self, request: Request) -> Response:
        data = TransactionApplicationSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        print(data.validated_data)

        blueprint = Blueprint()
        blueprint.entries.append(BlueprintEntry(
            model=data.validated_data["provider_model"],
            state=BlueprintEntryDesiredState.PRESENT,
            identifiers={},
            id="provider",
            attrs=data.validated_data["provider"],
        ))
        app_data = data.validated_data["app"]
        app_data["provider"] = KeyOf(None, ScalarNode(value="provider"))
        blueprint.entries.append(BlueprintEntry(
            model="authentik_core.application",
            state=BlueprintEntryDesiredState.PRESENT,
            identifiers={},
            attrs=app_data,
        ))
        importer = Importer("", {})
        return Response(status=200)
