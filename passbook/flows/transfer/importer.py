"""Flow importer"""
from json import loads
from typing import Any, Dict

from dacite import from_dict
from dacite.exceptions import DaciteError
from django.apps import apps
from django.db import transaction
from django.db.models import Model
from django.db.models.query_utils import Q
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer, Serializer
from structlog import BoundLogger, get_logger

from passbook.flows.models import Flow, FlowStageBinding, Stage
from passbook.flows.transfer.common import (
    EntryInvalidError,
    FlowBundle,
    FlowBundleEntry,
)
from passbook.lib.models import SerializerModel
from passbook.policies.models import Policy, PolicyBinding
from passbook.stages.prompt.models import Prompt

ALLOWED_MODELS = (Flow, FlowStageBinding, Stage, Policy, PolicyBinding, Prompt)


class FlowImporter:
    """Import Flow from json"""

    __import: FlowBundle

    __pk_map: Dict[Any, Model]

    logger: BoundLogger

    def __init__(self, json_input: str):
        self.logger = get_logger()
        self.__pk_map = {}
        import_dict = loads(json_input)
        try:
            self.__import = from_dict(FlowBundle, import_dict)
        except DaciteError as exc:
            raise EntryInvalidError from exc

    def __update_pks_for_attrs(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Replace any value if it is a known primary key of an other object"""
        def updater(value) -> Any:
            if value in self.__pk_map:
                self.logger.debug(
                    "updating reference in entry", value=value
                )
                return self.__pk_map[value]
            return value

        for key, value in attrs.items():
            if isinstance(value, (list, dict)):
                for idx, _inner_value in enumerate(value):
                    attrs[key][idx] = updater(_inner_value)
            else:
                attrs[key] = updater(value)
        return attrs

    def __query_from_identifier(self, attrs: Dict[str, Any]) -> Q:
        """Generate an or'd query from all identifiers in an entry"""
        # Since identifiers can also be pk-references to other objects (see FlowStageBinding)
        # we have to ensure those references are also replaced
        main_query = Q(pk=attrs["pk"])
        sub_query = Q()
        for identifier, value in attrs.items():
            if identifier == "pk":
                continue
            sub_query &= Q(**{identifier: value})
        return main_query | sub_query

    def _validate_single(self, entry: FlowBundleEntry) -> BaseSerializer:
        """Validate a single entry"""
        model_app_label, model_name = entry.model.split(".")
        model: SerializerModel = apps.get_model(model_app_label, model_name)
        if not isinstance(model(), ALLOWED_MODELS):
            raise EntryInvalidError(f"Model {model} not allowed")

        # If we try to validate without referencing a possible instance
        # we'll get a duplicate error, hence we load the model here and return
        # the full serializer for later usage
        # Because a model might have multiple unique columns, we chain all identifiers together
        # to create an OR query.
        updated_identifiers = self.__update_pks_for_attrs(entry.identifiers)
        existing_models = model.objects.filter(
            self.__query_from_identifier(updated_identifiers)
        )

        serializer_kwargs = {}
        if existing_models.exists():
            model_instance = existing_models.first()
            self.logger.debug(
                "initialise serializer with instance",
                model=model,
                instance=model_instance,
                pk=model_instance.pk,
            )
            serializer_kwargs["instance"] = model_instance
        else:
            self.logger.debug(
                "initialise new instance", model=model, **updated_identifiers
            )
        full_data = self.__update_pks_for_attrs(entry.attrs)
        full_data.update(updated_identifiers)
        serializer_kwargs["data"] = full_data

        serializer: Serializer = model().serializer(**serializer_kwargs)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            raise EntryInvalidError(f"Serializer errors {serializer.errors}") from exc
        return serializer

    def apply(self) -> bool:
        """Apply (create/update) flow json, in database transaction"""
        sid = transaction.savepoint()
        successful = self._apply_models()
        if not successful:
            self.logger.debug("Reverting changes due to error")
            transaction.savepoint_rollback(sid)
            return False
        self.logger.debug("Committing changes")
        transaction.savepoint_commit(sid)
        return True

    def _apply_models(self) -> bool:
        """Apply (create/update) flow json"""
        self.__pk_map = {}
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
            self.__pk_map[entry.identifiers["pk"]] = model.pk
            self.logger.debug("updated model", model=model, pk=model.pk)
        return True

    def validate(self) -> bool:
        """Validate loaded flow export, ensure all models are allowed
        and serializers have no errors"""
        self.logger.debug("Starting flow import validaton")
        if self.__import.version != 1:
            self.logger.warning("Invalid bundle version")
            return False
        sid = transaction.savepoint()
        successful = self._apply_models()
        if not successful:
            self.logger.debug("Flow validation failed")
        transaction.savepoint_rollback(sid)
        return successful
