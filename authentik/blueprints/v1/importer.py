"""Blueprint importer"""
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Optional

from dacite.core import from_dict
from dacite.exceptions import DaciteError
from deepmerge import always_merger
from django.db import transaction
from django.db.models import Model
from django.db.models.query_utils import Q
from django.db.utils import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer, Serializer
from structlog.stdlib import BoundLogger, get_logger
from structlog.testing import capture_logs
from structlog.types import EventDict
from yaml import load

from authentik.blueprints.v1.common import (
    Blueprint,
    BlueprintEntry,
    BlueprintEntryState,
    BlueprintLoader,
    EntryInvalidError,
)
from authentik.blueprints.v1.meta.registry import BaseMetaModel, registry
from authentik.core.models import (
    AuthenticatedSession,
    PropertyMapping,
    Provider,
    Source,
    UserSourceConnection,
)
from authentik.flows.models import Stage
from authentik.lib.models import SerializerModel
from authentik.outposts.models import OutpostServiceConnection
from authentik.policies.models import Policy, PolicyBindingModel


def is_model_allowed(model: type[Model]) -> bool:
    """Check if model is allowed"""
    # pylint: disable=imported-auth-user
    from django.contrib.auth.models import Group as DjangoGroup
    from django.contrib.auth.models import User as DjangoUser

    excluded_models = (
        DjangoUser,
        DjangoGroup,
        # Base classes
        Provider,
        Source,
        PropertyMapping,
        UserSourceConnection,
        Stage,
        OutpostServiceConnection,
        Policy,
        PolicyBindingModel,
        # Classes that have other dependencies
        AuthenticatedSession,
    )
    return model not in excluded_models and issubclass(model, (SerializerModel, BaseMetaModel))


@contextmanager
def transaction_rollback():
    """Enters an atomic transaction and always triggers a rollback at the end of the block."""
    atomic = transaction.atomic()
    # pylint: disable=unnecessary-dunder-call
    atomic.__enter__()
    yield
    atomic.__exit__(IntegrityError, None, None)


class Importer:
    """Import Blueprint from YAML"""

    logger: BoundLogger

    def __init__(self, yaml_input: str, context: Optional[dict] = None):
        self.__pk_map: dict[Any, Model] = {}
        self.logger = get_logger()
        import_dict = load(yaml_input, BlueprintLoader)
        try:
            self.__import = from_dict(Blueprint, import_dict)
        except DaciteError as exc:
            raise EntryInvalidError from exc
        context = {}
        always_merger.merge(context, self.__import.context)
        if context:
            always_merger.merge(context, context)
        self.__import.context = context

    @property
    def blueprint(self) -> Blueprint:
        """Get imported blueprint"""
        return self.__import

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
        main_query = Q()
        if "pk" in attrs:
            main_query = Q(pk=attrs["pk"])
        sub_query = Q()
        for identifier, value in attrs.items():
            if isinstance(value, dict):
                continue
            if identifier == "pk":
                continue
            sub_query &= Q(**{identifier: value})
        return main_query | sub_query

    def _validate_single(self, entry: BlueprintEntry) -> BaseSerializer:
        """Validate a single entry"""
        model_app_label, model_name = entry.model.split(".")
        model: type[SerializerModel] = registry.get_model(model_app_label, model_name)
        # Don't use isinstance since we don't want to check for inheritance
        if not is_model_allowed(model):
            raise EntryInvalidError(f"Model {model} not allowed")
        if issubclass(model, BaseMetaModel):
            serializer_class: type[Serializer] = model.serializer()
            serializer = serializer_class(data=entry.get_attrs(self.__import))
            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as exc:
                raise EntryInvalidError(
                    f"Serializer errors {serializer.errors}", serializer_errors=serializer.errors
                ) from exc
            return serializer
        if entry.identifiers == {}:
            raise EntryInvalidError("No identifiers")

        # If we try to validate without referencing a possible instance
        # we'll get a duplicate error, hence we load the model here and return
        # the full serializer for later usage
        # Because a model might have multiple unique columns, we chain all identifiers together
        # to create an OR query.
        updated_identifiers = self.__update_pks_for_attrs(entry.get_identifiers(self.__import))
        for key, value in list(updated_identifiers.items()):
            if isinstance(value, dict) and "pk" in value:
                del updated_identifiers[key]
                updated_identifiers[f"{key}"] = value["pk"]
        existing_models = model.objects.filter(self.__query_from_identifier(updated_identifiers))

        serializer_kwargs = {}
        if not isinstance(model(), BaseMetaModel) and existing_models.exists():
            model_instance = existing_models.first()
            self.logger.debug(
                "initialise serializer with instance",
                model=model,
                instance=model_instance,
                pk=model_instance.pk,
            )
            serializer_kwargs["instance"] = model_instance
            serializer_kwargs["partial"] = True
        else:
            self.logger.debug(
                "initialised new serializer instance", model=model, **updated_identifiers
            )
            model_instance = model()
            # pk needs to be set on the model instance otherwise a new one will be generated
            if "pk" in updated_identifiers:
                model_instance.pk = updated_identifiers["pk"]
            serializer_kwargs["instance"] = model_instance
        full_data = self.__update_pks_for_attrs(entry.get_attrs(self.__import))
        full_data.update(updated_identifiers)
        serializer_kwargs["data"] = full_data

        serializer: Serializer = model().serializer(**serializer_kwargs)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            raise EntryInvalidError(
                f"Serializer errors {serializer.errors}", serializer_errors=serializer.errors
            ) from exc
        return serializer

    def apply(self) -> bool:
        """Apply (create/update) models yaml, in database transaction"""
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
        """Apply (create/update) models yaml"""
        self.__pk_map = {}
        for entry in self.__import.entries:
            model_app_label, model_name = entry.model.split(".")
            try:
                model: type[SerializerModel] = registry.get_model(model_app_label, model_name)
            except LookupError:
                self.logger.warning(
                    "app or model does not exist", app=model_app_label, model=model_name
                )
                return False
            # Validate each single entry
            try:
                serializer = self._validate_single(entry)
            except EntryInvalidError as exc:
                self.logger.warning(f"entry invalid: {exc}", entry=entry, error=exc)
                return False

            model = serializer.save()
            if "pk" in entry.identifiers:
                self.__pk_map[entry.identifiers["pk"]] = model.pk
            entry._state = BlueprintEntryState(model)
            self.logger.debug("updated model", model=model)
        return True

    def validate(self) -> tuple[bool, list[EventDict]]:
        """Validate loaded blueprint export, ensure all models are allowed
        and serializers have no errors"""
        self.logger.debug("Starting blueprint import validation")
        orig_import = deepcopy(self.__import)
        if self.__import.version != 1:
            self.logger.warning("Invalid blueprint version")
            return False, []
        with (
            transaction_rollback(),
            capture_logs() as logs,
        ):
            successful = self._apply_models()
            if not successful:
                self.logger.debug("Blueprint validation failed")
        for log in logs:
            getattr(self.logger, log.get("log_level"))(**log)
        self.__import = orig_import
        return successful, logs
