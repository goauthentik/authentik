from typing import Any

from django.db.models import QuerySet

from akql.ast import Logical
from akql.parser import AKQLParser
from akql.schema import AKQLField, AKQLSchema


def build_filter(expr: str, schema_instance: AKQLSchema):
    if isinstance(expr.operator, Logical):
        left = build_filter(expr.left, schema_instance)
        right = build_filter(expr.right, schema_instance)
        if expr.operator.operator == "or":
            return left | right
        else:
            return left & right

    field = schema_instance.resolve_name(expr.left)
    if not field:
        # That must be a reference to a model without specifying a field.
        # Let's construct an abstract lookup field for it
        field = AKQLField(
            name=expr.left.parts[-1],
            nullable=True,
        )
    return field.get_lookup(
        path=expr.left.parts[:-1],
        operator=expr.operator.operator,
        value=expr.right.value,
    )


def apply_search(
    queryset: QuerySet,
    search: str,
    context: dict[str, Any] | None = None,
    schema: type[AKQLSchema] | None = None,
) -> QuerySet:
    """
    Applies search written in DjangoQL mini-language to given queryset
    """
    ast = AKQLParser(context=context).parse(search)
    schema = schema or AKQLSchema
    schema_instance = schema(queryset.model)
    schema_instance.validate(ast)
    return queryset.filter(build_filter(ast, schema_instance))
