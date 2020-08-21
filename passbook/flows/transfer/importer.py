"""Flow importer"""
from json import loads
from typing import Type

from dacite import from_dict
from dacite.exceptions import DaciteError
from django.apps import apps
from django.db import transaction
from django.db.models import Model
from rest_framework.serializers import BaseSerializer, Serializer
from structlog import BoundLogger, get_logger

from passbook.flows.models import Flow, FlowStageBinding, Stage
from passbook.flows.transfer.common import (
    EntryInvalidError,
    FlowBundle,
    FlowBundleEntry,
)
from passbook.lib.models import SerializerModel
from passbook.policies.models import Policy, PolicyBinding, PolicyBindingModel
from passbook.stages.prompt.models import Prompt

ALLOWED_MODELS = (Flow, FlowStageBinding, Stage, Policy, PolicyBinding, Prompt)


class FlowImporter:
    """Import Flow from json"""

    __import: FlowBundle

    logger: BoundLogger

    def __init__(self, json_input: str):
        self.logger = get_logger()
        import_dict = loads(json_input)
        try:
            self.__import = from_dict(FlowBundle, import_dict)
        except DaciteError as exc:
            raise EntryInvalidError from exc

    def validate(self) -> bool:
        """Validate loaded flow export, ensure all models are allowed
        and serializers have no errors"""
        if self.__import.version != 1:
            self.logger.warning("Invalid bundle version")
            return False
        for entry in self.__import.entries:
            try:
                self._validate_single(entry)
            except EntryInvalidError as exc:
                self.logger.warning(exc)
                return False
        return True

    def __get_pk_filed(self, model_class: Type[Model]) -> str:
        fields = model_class._meta.get_fields()
        pks = []
        for field in fields:
            # Ignore base PK from pbm as that isn't the same pk we exported
            if field.model in [PolicyBindingModel]:
                continue
            # Ignore primary keys with _ptr suffix as those are surrogate and not what we exported
            if field.name.endswith("_ptr"):
                continue
            if hasattr(field, "primary_key"):
                if field.primary_key:
                    pks.append(field.name)
        if len(pks) > 1:
            self.logger.debug(
                "Found more than one fields with primary_key=True, using pk", pks=pks
            )
            return "pk"
        return pks[0]

    def _validate_single(self, entry: FlowBundleEntry) -> BaseSerializer:
        """Validate a single entry"""
        model_app_label, model_name = entry.model.split(".")
        model: SerializerModel = apps.get_model(model_app_label, model_name)
        if not isinstance(model(), ALLOWED_MODELS):
            raise EntryInvalidError(f"Model {model} not allowed")

        # If we try to validate without referencing a possible instance
        # we'll get a duplicate error, hence we load the model here and return
        # the full serializer for later usage
        existing_models = model.objects.filter(pk=entry.identifier)
        serializer_kwargs = {"data": entry.attrs}
        if existing_models.exists():
            self.logger.debug(
                "initialise serializer with instance", instance=existing_models.first()
            )
            serializer_kwargs["instance"] = existing_models.first()
        else:
            self.logger.debug("initialise new instance", pk=entry.identifier)

        serializer: Serializer = model().serializer(**serializer_kwargs)
        is_valid = serializer.is_valid()
        if not is_valid:
            raise EntryInvalidError(f"Serializer errors {serializer.errors}")
        if not existing_models.exists():
            # only insert the PK if we're creating a new model, otherwise we get
            # an integrity error
            model_pk = self.__get_pk_filed(model)
            serializer.validated_data[model_pk] = entry.identifier
        return serializer

    def apply(self) -> bool:
        """Apply (create/update) flow json, in database transaction"""
        transaction.set_autocommit(False)
        successful = self._apply_models()
        if not successful:
            self.logger.debug("Reverting changes due to error")
            transaction.rollback()
            transaction.set_autocommit(True)
            return False
        self.logger.debug("Committing changes")
        transaction.commit()
        transaction.set_autocommit(True)
        return True

    def _apply_models(self) -> bool:
        """Apply (create/update) flow json"""
        for entry in self.__import.entries:
            model_app_label, model_name = entry.model.split(".")
            model: SerializerModel = apps.get_model(model_app_label, model_name)
            # Validate each single entry
            try:
                serializer = self._validate_single(entry)
            except EntryInvalidError as exc:
                self.logger.error("entry not valid", entry=entry, error=exc)
                return False

            model = serializer.save()
            self.logger.debug("updated model", model=model, pk=model.pk)
        return True
