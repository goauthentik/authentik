"""Flow importer"""
from contextlib import contextmanager
from copy import deepcopy
from json import loads
from typing import Any

from dacite import from_dict
from dacite.exceptions import DaciteError
from django.apps import apps
from django.db import transaction
from django.db.models import Model
from django.db.models.query_utils import Q
from django.db.utils import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer, Serializer
from structlog.stdlib import BoundLogger, get_logger

from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.flows.transfer.common import EntryInvalidError, FlowBundle, FlowBundleEntry
from authentik.lib.models import SerializerModel
from authentik.policies.models import Policy, PolicyBinding
from authentik.stages.prompt.models import Prompt

ALLOWED_MODELS = (Flow, FlowStageBinding, Stage, Policy, PolicyBinding, Prompt)


@contextmanager
def transaction_rollback():
    """Enters an atomic transaction and always triggers a rollback at the end of the block."""
    atomic = transaction.atomic()
    # pylint: disable=unnecessary-dunder-call
    atomic.__enter__()
    yield
    atomic.__exit__(IntegrityError, None, None)


class FlowImporter:
    """Import Flow from json"""

    logger: BoundLogger

    def __init__(self, json_input: str):
        self.__pk_map: dict[Any, Model] = {}
        self.logger = get_logger()
        import_dict = loads(json_input)
        try:
            self.__import = from_dict(FlowBundle, import_dict)
        except DaciteError as exc:
            raise EntryInvalidError from exc

    def __update_pks_for_attrs(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Replace any value if it is a known primary key of an other object"""

        def updater(value) -> Any:
            if value in self.__pk_map:
                self.logger.debug("updating reference in entry", value=value)
                return self.__pk_map[value]
            return value

        for key, value in attrs.items():
            try:
                if isinstance(value, dict):
                    for idx, _inner_key in enumerate(value):
                        value[_inner_key] = updater(value[_inner_key])
                elif isinstance(value, list):
                    for idx, _inner_value in enumerate(value):
                        attrs[key][idx] = updater(_inner_value)
                else:
                    attrs[key] = updater(value)
            except TypeError:
                continue
        return attrs

    def __query_from_identifier(self, attrs: dict[str, Any]) -> Q:
        """Generate an or'd query from all identifiers in an entry"""
        # Since identifiers can also be pk-references to other objects (see FlowStageBinding)
        # we have to ensure those references are also replaced
        main_query = Q(pk=attrs["pk"])
        sub_query = Q()
        for identifier, value in attrs.items():
            if isinstance(value, dict):
                continue
            if identifier == "pk":
                continue
            sub_query &= Q(**{identifier: value})
        return main_query | sub_query

    def _validate_single(self, entry: FlowBundleEntry) -> BaseSerializer:
        """Validate a single entry"""
        model_app_label, model_name = entry.model.split(".")
        model: type[SerializerModel] = apps.get_model(model_app_label, model_name)
        if not isinstance(model(), ALLOWED_MODELS):
            raise EntryInvalidError(f"Model {model} not allowed")

        # If we try to validate without referencing a possible instance
        # we'll get a duplicate error, hence we load the model here and return
        # the full serializer for later usage
        # Because a model might have multiple unique columns, we chain all identifiers together
        # to create an OR query.
        updated_identifiers = self.__update_pks_for_attrs(entry.identifiers)
        for key, value in list(updated_identifiers.items()):
            if isinstance(value, dict) and "pk" in value:
                del updated_identifiers[key]
                updated_identifiers[f"{key}"] = value["pk"]
        existing_models = model.objects.filter(self.__query_from_identifier(updated_identifiers))

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
            self.logger.debug("initialise new instance", model=model, **updated_identifiers)
            model_instance = model()
            # pk needs to be set on the model instance otherwise a new one will be generated
            if "pk" in updated_identifiers:
                model_instance.pk = updated_identifiers["pk"]
            serializer_kwargs["instance"] = model_instance
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
        try:
            with transaction.atomic():
                if not self._apply_models():
                    self.logger.debug("Reverting changes due to error")
                    raise IntegrityError
        except IntegrityError:
            return False
        else:
            self.logger.debug("Committing changes")
        return True

    def _apply_models(self) -> bool:
        """Apply (create/update) flow json"""
        self.__pk_map = {}
        entries = deepcopy(self.__import.entries)
        for entry in entries:
            model_app_label, model_name = entry.model.split(".")
            try:
                model: SerializerModel = apps.get_model(model_app_label, model_name)
            except LookupError:
                self.logger.warning(
                    "app or model does not exist", app=model_app_label, model=model_name
                )
                return False
            # Validate each single entry
            try:
                serializer = self._validate_single(entry)
            except EntryInvalidError as exc:
                self.logger.warning("entry not valid", entry=entry, error=exc)
                return False

            model = serializer.save()
            self.__pk_map[entry.identifiers["pk"]] = model.pk
            self.logger.debug("updated model", model=model, pk=model.pk)
        return True

    def validate(self) -> bool:
        """Validate loaded flow export, ensure all models are allowed
        and serializers have no errors"""
        self.logger.debug("Starting flow import validation")
        if self.__import.version != 1:
            self.logger.warning("Invalid bundle version")
            return False
        with transaction_rollback():
            successful = self._apply_models()
            if not successful:
                self.logger.debug("Flow validation failed")
        return successful
