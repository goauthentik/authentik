"""Blueprint importer"""
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Optional

from dacite.config import Config
from dacite.core import from_dict
from dacite.exceptions import DaciteError
from deepmerge import always_merger
from django.core.exceptions import FieldError
from django.db.models import Model
from django.db.models.query_utils import Q
from django.db.transaction import atomic
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
    BlueprintEntryDesiredState,
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
from authentik.events.utils import cleanse_dict
from authentik.flows.models import FlowToken, Stage
from authentik.lib.models import SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.outposts.models import OutpostServiceConnection
from authentik.policies.models import Policy, PolicyBindingModel

# Context set when the serializer is created in a blueprint context
# Update website/developer-docs/blueprints/v1/models.md when used
SERIALIZER_CONTEXT_BLUEPRINT = "blueprint_entry"


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
        # Classes which are only internally managed
        FlowToken,
    )
    return model not in excluded_models and issubclass(model, (SerializerModel, BaseMetaModel))


class DoRollback(SentryIgnoredException):
    """Exception to trigger a rollback"""


@contextmanager
def transaction_rollback():
    """Enters an atomic transaction and always triggers a rollback at the end of the block."""
    try:
        with atomic():
            yield
            raise DoRollback()
    except DoRollback:
        pass


class Importer:
    """Import Blueprint from raw dict or YAML/JSON"""

    logger: BoundLogger
    _import: Blueprint

    def __init__(self, blueprint: Blueprint, context: Optional[dict] = None):
        self.__pk_map: dict[Any, Model] = {}
        self._import = blueprint
        self.logger = get_logger()
        ctx = {}
        always_merger.merge(ctx, self._import.context)
        if context:
            always_merger.merge(ctx, context)
        self._import.context = ctx

    @staticmethod
    def from_string(yaml_input: str, context: dict | None = None) -> "Importer":
        """Parse YAML string and create blueprint importer from it"""
        import_dict = load(yaml_input, BlueprintLoader)
        try:
            _import = from_dict(
                Blueprint, import_dict, config=Config(cast=[BlueprintEntryDesiredState])
            )
        except DaciteError as exc:
            raise EntryInvalidError from exc
        return Importer(_import, context)

    @property
    def blueprint(self) -> Blueprint:
        """Get imported blueprint"""
        return self._import

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
            if identifier == "pk":
                continue
            if isinstance(value, dict):
                sub_query &= Q(**{f"{identifier}__contains": value})
            else:
                sub_query &= Q(**{identifier: value})

        return main_query | sub_query

    # pylint: disable-msg=too-many-locals
    def _validate_single(self, entry: BlueprintEntry) -> Optional[BaseSerializer]:
        """Validate a single entry"""
        if not entry.check_all_conditions_match(self._import):
            self.logger.debug("One or more conditions of this entry are not fulfilled, skipping")
            return None

        model_app_label, model_name = entry.get_model(self._import).split(".")
        model: type[SerializerModel] = registry.get_model(model_app_label, model_name)
        # Don't use isinstance since we don't want to check for inheritance
        if not is_model_allowed(model):
            raise EntryInvalidError.from_entry(f"Model {model} not allowed", entry)
        if issubclass(model, BaseMetaModel):
            serializer_class: type[Serializer] = model.serializer()
            serializer = serializer_class(
                data=entry.get_attrs(self._import),
                context={
                    SERIALIZER_CONTEXT_BLUEPRINT: entry,
                },
            )
            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as exc:
                raise EntryInvalidError.from_entry(
                    f"Serializer errors {serializer.errors}",
                    validation_error=exc,
                    entry=entry,
                ) from exc
            return serializer

        # If we try to validate without referencing a possible instance
        # we'll get a duplicate error, hence we load the model here and return
        # the full serializer for later usage
        # Because a model might have multiple unique columns, we chain all identifiers together
        # to create an OR query.
        updated_identifiers = self.__update_pks_for_attrs(entry.get_identifiers(self._import))
        for key, value in list(updated_identifiers.items()):
            if isinstance(value, dict) and "pk" in value:
                del updated_identifiers[key]
                updated_identifiers[f"{key}"] = value["pk"]

        query = self.__query_from_identifier(updated_identifiers)
        if not query:
            raise EntryInvalidError.from_entry("No or invalid identifiers", entry)

        try:
            existing_models = model.objects.filter(query)
        except FieldError as exc:
            raise EntryInvalidError.from_entry(f"Invalid identifier field: {exc}", entry) from exc

        serializer_kwargs = {}
        model_instance = existing_models.first()
        if not isinstance(model(), BaseMetaModel) and model_instance:
            self.logger.debug(
                "initialise serializer with instance",
                model=model,
                instance=model_instance,
                pk=model_instance.pk,
            )
            serializer_kwargs["instance"] = model_instance
            serializer_kwargs["partial"] = True
        elif model_instance and entry.state == BlueprintEntryDesiredState.MUST_CREATED:
            raise EntryInvalidError.from_entry(
                (
                    f"state is set to {BlueprintEntryDesiredState.MUST_CREATED} "
                    "and object exists already",
                ),
                entry,
            )
        else:
            self.logger.debug(
                "initialised new serializer instance",
                model=model,
                **cleanse_dict(updated_identifiers),
            )
            model_instance = model()
            # pk needs to be set on the model instance otherwise a new one will be generated
            if "pk" in updated_identifiers:
                model_instance.pk = updated_identifiers["pk"]
            serializer_kwargs["instance"] = model_instance
        try:
            full_data = self.__update_pks_for_attrs(entry.get_attrs(self._import))
        except ValueError as exc:
            raise EntryInvalidError.from_entry(exc, entry) from exc
        always_merger.merge(full_data, updated_identifiers)
        serializer_kwargs["data"] = full_data

        serializer: Serializer = model().serializer(
            context={
                SERIALIZER_CONTEXT_BLUEPRINT: entry,
            },
            **serializer_kwargs,
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            raise EntryInvalidError.from_entry(
                f"Serializer errors {serializer.errors}",
                validation_error=exc,
                entry=entry,
            ) from exc
        return serializer

    def apply(self) -> bool:
        """Apply (create/update) models yaml, in database transaction"""
        try:
            with atomic():
                if not self._apply_models():
                    self.logger.debug("Reverting changes due to error")
                    raise IntegrityError
        except IntegrityError:
            return False
        self.logger.debug("Committing changes")
        return True

    def _apply_models(self, raise_errors=False) -> bool:
        """Apply (create/update) models yaml"""
        self.__pk_map = {}
        for entry in self._import.entries:
            model_app_label, model_name = entry.get_model(self._import).split(".")
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
                # For deleting objects we don't need the serializer to be valid
                if entry.get_state(self._import) == BlueprintEntryDesiredState.ABSENT:
                    continue
                self.logger.warning(f"entry invalid: {exc}", entry=entry, error=exc)
                if raise_errors:
                    raise exc
                return False
            if not serializer:
                continue

            state = entry.get_state(self._import)
            if state in [
                BlueprintEntryDesiredState.PRESENT,
                BlueprintEntryDesiredState.CREATED,
                BlueprintEntryDesiredState.MUST_CREATED,
            ]:
                instance = serializer.instance
                if (
                    instance
                    and not instance._state.adding
                    and state == BlueprintEntryDesiredState.CREATED
                ):
                    self.logger.debug(
                        "instance exists, skipping",
                        model=model,
                        instance=instance,
                        pk=instance.pk,
                    )
                else:
                    instance = serializer.save()
                    self.logger.debug("updated model", model=instance)
                if "pk" in entry.identifiers:
                    self.__pk_map[entry.identifiers["pk"]] = instance.pk
                entry._state = BlueprintEntryState(instance)
            elif state == BlueprintEntryDesiredState.ABSENT:
                instance: Optional[Model] = serializer.instance
                if instance.pk:
                    instance.delete()
                    self.logger.debug("deleted model", mode=instance)
                    continue
                self.logger.debug("entry to delete with no instance, skipping")
        return True

    def validate(self, raise_validation_errors=False) -> tuple[bool, list[EventDict]]:
        """Validate loaded blueprint export, ensure all models are allowed
        and serializers have no errors"""
        self.logger.debug("Starting blueprint import validation")
        orig_import = deepcopy(self._import)
        if self._import.version != 1:
            self.logger.warning("Invalid blueprint version")
            return False, [{"event": "Invalid blueprint version"}]
        with (
            transaction_rollback(),
            capture_logs() as logs,
        ):
            successful = self._apply_models(raise_errors=raise_validation_errors)
            if not successful:
                self.logger.debug("Blueprint validation failed")
        for log in logs:
            getattr(self.logger, log.get("log_level"))(**log)
        self.logger.debug("Finished blueprint import validation")
        self._import = orig_import
        return successful, logs
