from django.db.models import QuerySet

from .ast import Logical
from .parser import DjangoQLParser
from .schema import DjangoQLField, DjangoQLSchema


def build_filter(expr, schema_instance):
    if isinstance(expr.operator, Logical):
        left = build_filter(expr.left, schema_instance)
        right = build_filter(expr.right, schema_instance)
        if expr.operator.operator == 'or':
            return left | right
        else:
            return left & right

    field = schema_instance.resolve_name(expr.left)
    if not field:
        # That must be a reference to a model without specifying a field.
        # Let's construct an abstract lookup field for it
        field = DjangoQLField(
            name=expr.left.parts[-1],
            nullable=True,
        )
    return field.get_lookup(
        path=expr.left.parts[:-1],
        operator=expr.operator.operator,
        value=expr.right.value,
    )


def apply_search(queryset, search, schema=None):
    """
    Applies search written in DjangoQL mini-language to given queryset
    """
    ast = DjangoQLParser().parse(search)
    schema = schema or DjangoQLSchema
    schema_instance = schema(queryset.model)
    schema_instance.validate(ast)
    return queryset.filter(build_filter(ast, schema_instance))


class DjangoQLQuerySet(QuerySet):
    djangoql_schema = None

    def djangoql(self, search, schema=None):
        return apply_search(self, search, schema=schema or self.djangoql_schema)
