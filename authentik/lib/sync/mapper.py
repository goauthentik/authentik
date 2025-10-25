from collections.abc import Generator

from django.db.models import QuerySet
from django.http import HttpRequest

from authentik.core.expression.evaluator import PropertyMappingEvaluator
from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
)
from authentik.core.models import PropertyMapping, User
from authentik.lib.expression.exceptions import ControlFlowException


class PropertyMappingManager:
    """Pre-compile and cache property mappings when an identical
    set is used multiple times"""

    query_set: QuerySet[PropertyMapping]
    mapping_subclass: type[PropertyMapping]

    _evaluators: list[PropertyMappingEvaluator]

    globals: dict

    __has_compiled: bool

    def __init__(
        self,
        qs: QuerySet[PropertyMapping],
        # Expected subclass of PropertyMappings, any objects in the queryset
        # that are not an instance of this class will be discarded
        mapping_subclass: type[PropertyMapping],
        # As they keys of parameters are part of the compilation,
        # we need a list of all parameter names that will be used during evaluation
        context_keys: list[str],
    ) -> None:
        self.query_set = qs.order_by("name")
        self.mapping_subclass = mapping_subclass
        self.context_keys = context_keys
        self.globals = {}
        self.__has_compiled = False

    def compile(self):
        self._evaluators = []
        for mapping in self.query_set:
            if not isinstance(mapping, self.mapping_subclass):
                continue
            evaluator = PropertyMappingEvaluator(
                mapping, **{key: None for key in self.context_keys}
            )
            evaluator._globals.update(self.globals)
            # Compile and cache expression
            evaluator.compile()
            self._evaluators.append(evaluator)

    def iter_eval(
        self,
        user: User | None,
        request: HttpRequest | None,
        return_mapping: bool = False,
        **kwargs,
    ) -> Generator[tuple[dict, PropertyMapping]]:
        """Iterate over all mappings that were pre-compiled and
        execute all of them with the given context"""
        if not self.__has_compiled:
            self.compile()
            self.__has_compiled = True
        for mapping in self._evaluators:
            mapping.set_context(user, request, **kwargs)
            try:
                value = mapping.evaluate(mapping.model.expression)
            except (PropertyMappingExpressionException, ControlFlowException) as exc:
                raise exc from exc
            except Exception as exc:
                raise PropertyMappingExpressionException(exc, mapping.model) from exc
            if value is None:
                continue
            if return_mapping:
                yield value, mapping.model
            else:
                yield value
