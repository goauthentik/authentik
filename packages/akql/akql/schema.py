import inspect
import warnings
from collections import OrderedDict, defaultdict, deque
from collections.abc import Generator
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import connection, models
from django.db.models import ManyToManyRel, ManyToOneRel, Model, Q
from django.db.models.fields.related import ForeignObjectRel
from django.utils.timezone import get_current_timezone

from akql.ast import Comparison, Const, List, Logical, Name, Node
from akql.exceptions import DjangoQLSchemaError


class DjangoQLField:
    """
    Abstract searchable field
    """

    model = None
    name = None
    nullable = False
    suggest_options = False
    type = "unknown"
    value_types = []
    value_types_description = ""

    def __init__(self, model=None, name=None, nullable=None, suggest_options=None):
        if model is not None:
            self.model = model
        if name is not None:
            self.name = name
        if nullable is not None:
            self.nullable = nullable
        if suggest_options is not None:
            self.suggest_options = suggest_options

    def _field_choices(self):
        if self.model:
            try:
                return self.model._meta.get_field(self.name).choices
            except (AttributeError, FieldDoesNotExist):
                pass
        return []

    @property
    def async_options(self):
        return not self._field_choices()

    def get_options(self, search):
        """
        Override this method to provide custom suggestion options
        """
        result = []
        choices = self._field_choices()
        if choices:
            search = search.lower()
            for c in choices:
                choice = str(c[1])
                if search in choice.lower():
                    result.append(choice)
        return result

    def get_lookup_name(self):
        """
        Override this method to provide custom lookup name
        """
        return self.name

    def get_lookup_value(self, value):
        """
        Override this method to convert displayed values to lookup values
        """
        choices = self._field_choices()
        if choices:
            if isinstance(value, list):
                return [c[0] for c in choices if c[0] in value or c[1] in value]
            else:
                for c in choices:
                    if value in c:
                        return c[0]
        return value

    def get_operator(self, operator):
        """
        Get a comparison suffix to be used in Django ORM & inversion flag for it

        :param operator: string, DjangoQL comparison operator
        :return: (suffix, invert) - a tuple with 2 values:
            suffix - suffix to be used in ORM query, for example '__gt' for '>'
            invert - boolean, True if this comparison needs to be inverted
        """
        op = {
            "=": "",
            ">": "__gt",
            ">=": "__gte",
            "<": "__lt",
            "<=": "__lte",
            "~": "__icontains",
            "in": "__in",
            "startswith": "__istartswith",
            "endswith": "__iendswith",
        }.get(operator)
        if op is not None:
            return op, False
        op = {
            "!=": "",
            "!~": "__icontains",
            "not in": "__in",
            "not startswith": "__istartswith",
            "not endswith": "__iendswith",
        }[operator]
        return op, True

    def get_lookup(self, path, operator, value):
        """
        Performs a lookup for this field with given path, operator and value.

        Override this if you'd like to implement a fully custom lookup. It
        should support all comparison operators compatible with the field type.

        :param path: a list of names preceding current lookup. For example,
            if expression looks like 'author.groups.name = "Foo"' path would
            be ['author', 'groups']. 'name' is not included, because it's the
            current field instance itself.
        :param operator: a string with comparison operator. It could be one of
            the following: '=', '!=', '>', '>=', '<', '<=', '~', '!~', 'in',
            'not in'. Depending on the field type, some operators may be
            excluded. '~' and '!~' can be applied to StrField only and aren't
            allowed for any other fields. BoolField can't be used with less or
            greater operators, '>', '>=', '<' and '<=' are excluded for it.
        :param value: value passed for comparison
        :return: Q-object
        """
        search = "__".join(path + [self.get_lookup_name()])
        op, invert = self.get_operator(operator)
        q = models.Q(**{f"{search}{op}": self.get_lookup_value(value)})
        return ~q if invert else q

    def validate(self, value):
        if not self.nullable and value is None:
            raise DjangoQLSchemaError(
                f"Field {self.name} is not nullable, " "can't compare it to None",
            )
        if value is not None and type(value) not in self.value_types:
            if self.nullable:
                msg = (
                    'Field "{field}" has "nullable {field_type}" type. '
                    "It can be compared to {possible_values} or None, "
                    "but not to {value}"
                )
            else:
                msg = (
                    'Field "{field}" has "{field_type}" type. It can '
                    "be compared to {possible_values}, "
                    "but not to {value}"
                )
            raise DjangoQLSchemaError(
                msg.format(
                    field=self.name,
                    field_type=self.type,
                    possible_values=self.value_types_description,
                    value=repr(value),
                )
            )


class IntField(DjangoQLField):
    type = "int"
    value_types = [int]
    value_types_description = "integer numbers"

    def validate(self, value):
        """
        Support enum-like choices defined on an integer field
        """
        return super().validate(self.get_lookup_value(value))


class FloatField(DjangoQLField):
    type = "float"
    value_types = [int, float, Decimal]
    value_types_description = "floating point numbers"


class StrField(DjangoQLField):
    type = "str"
    value_types = [str]
    value_types_description = "strings"

    def get_options(self, search):
        choice_options = super().get_options(search)
        if choice_options:
            return choice_options
        lookup = {}
        if search:
            lookup[f"{self.name}__icontains"] = search
        return (
            self.model.objects.filter(**lookup)
            .order_by(self.name)
            .values_list(self.name, flat=True)
            .distinct()
        )


class BoolField(DjangoQLField):
    type = "bool"
    value_types = [bool]
    value_types_description = "True or False"


class DateField(DjangoQLField):
    type = "date"
    value_types = [str]
    value_types_description = 'dates in "YYYY-MM-DD" format'

    def validate(self, value):
        super().validate(value)
        try:
            self.get_lookup_value(value)
        except ValueError as exc:
            raise DjangoQLSchemaError(
                f'Field "{self.name}" can be compared to dates in '
                f'"YYYY-MM-DD" format, but not to {repr(value)}',
            ) from exc

    def get_lookup_value(self, value):
        if not value:
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()


class DateTimeField(DjangoQLField):
    type = "datetime"
    value_types = [str]
    value_types_description = 'timestamps in "YYYY-MM-DD HH:MM" format'

    def validate(self, value):
        super().validate(value)
        try:
            self.get_lookup_value(value)
        except ValueError as exc:
            raise DjangoQLSchemaError(
                f'Field "{self.name}" can be compared to timestamps in '
                f'"YYYY-MM-DD HH:MM" format, but not to {repr(value)}',
            ) from exc

    def get_lookup_value(self, value):
        if not value:
            return None
        mask = "%Y-%m-%d"
        if len(value) > 10:
            mask += " %H:%M"
        if len(value) > 16:
            mask += ":%S"
        dt = datetime.strptime(value, mask)
        if settings.USE_TZ:
            dt = dt.replace(tzinfo=get_current_timezone())
        return dt

    def get_lookup(self, path, operator, value):
        search = "__".join(path + [self.get_lookup_name()])
        op, invert = self.get_operator(operator)

        # Add LIKE operator support for datetime fields. For LIKE comparisons
        # we don't want to convert source value to datetime instance, because
        # it would effectively kill the idea. What we want is expressions like
        #       'created ~ "2017-01-30'
        # to be translated to
        #       'created LIKE %2017-01-30%',
        # but it would work only if we pass a string as a parameter. If we pass
        # a datetime instance, it would add time part in a form of 00:00:00,
        # and resulting comparison would look like
        #       'created LIKE %2017-01-30 00:00:00%'
        # which is not what we want for this case.
        val = value if operator in ("~", "!~") else self.get_lookup_value(value)

        q = models.Q(**{f"{search}{op}": val})
        return ~q if invert else q


class RelationField(DjangoQLField):
    type = "relation"

    def __init__(self, model, name, related_model, nullable=False, suggest_options=False):
        super().__init__(
            model=model,
            name=name,
            nullable=nullable,
            suggest_options=suggest_options,
        )
        self.related_model = related_model

    @property
    def relation(self):
        return DjangoQLSchema.model_label(self.related_model)


class JSONSearchField(StrField):
    """JSON field for DjangoQL"""

    model: Model

    def __init__(self, model=None, name=None, nullable=None, suggest_nested=True):
        # Set this in the constructor to not clobber the type variable
        self.type = "relation"
        self.suggest_nested = suggest_nested
        super().__init__(model, name, nullable)

    def get_lookup(self, path, operator, value):
        search = "__".join(path)
        op, invert = self.get_operator(operator)
        q = Q(**{f"{search}{op}": self.get_lookup_value(value)})
        return ~q if invert else q

    def json_field_keys(self) -> Generator[tuple[str]]:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                WITH RECURSIVE "{self.name}_keys" AS (
                    SELECT
                        ARRAY[jsonb_object_keys("{self.name}")] AS key_path_array,
                        "{self.name}" -> jsonb_object_keys("{self.name}") AS value
                    FROM {self.model._meta.db_table}
                    WHERE "{self.name}" IS NOT NULL
                        AND jsonb_typeof("{self.name}") = 'object'

                    UNION ALL

                    SELECT
                        ck.key_path_array || jsonb_object_keys(ck.value),
                        ck.value -> jsonb_object_keys(ck.value) AS value
                    FROM "{self.name}_keys" ck
                    WHERE jsonb_typeof(ck.value) = 'object'
                ),

                unique_paths AS (
                    SELECT DISTINCT key_path_array
                    FROM "{self.name}_keys"
                )

                SELECT key_path_array FROM unique_paths;
            """  # nosec
            )
            return (x[0] for x in cursor.fetchall())

    def get_nested_options(self) -> OrderedDict:
        """Get keys of all nested objects to show autocomplete"""
        if not self.suggest_nested:
            return OrderedDict()
        base_model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}_{self.name}"

        def recursive_function(parts: list[str], parent_parts: list[str] | None = None):
            if not parent_parts:
                parent_parts = []
            path = parts.pop(0)
            parent_parts.append(path)
            relation_key = "_".join(parent_parts)
            if len(parts) > 1:
                out_dict = {
                    relation_key: {
                        parts[0]: {
                            "type": "relation",
                            "relation": f"{relation_key}_{parts[0]}",
                        }
                    }
                }
                child_paths = recursive_function(parts.copy(), parent_parts.copy())
                child_paths.update(out_dict)
                return child_paths
            else:
                return {relation_key: {parts[0]: {}}}

        relation_structure = defaultdict(dict)

        for relations in self.json_field_keys():
            result = recursive_function([base_model_name] + relations)
            for relation_key, value in result.items():
                for sub_relation_key, sub_value in value.items():
                    if not relation_structure[relation_key].get(sub_relation_key, None):
                        relation_structure[relation_key][sub_relation_key] = sub_value
                    else:
                        relation_structure[relation_key][sub_relation_key].update(sub_value)

        final_dict = defaultdict(dict)

        for key, value in relation_structure.items():
            for sub_key, sub_value in value.items():
                if not sub_value:
                    final_dict[key][sub_key] = {
                        "type": "str",
                        "nullable": True,
                    }
                else:
                    final_dict[key][sub_key] = sub_value
        return OrderedDict(final_dict)

    def relation(self) -> str:
        return f"{self.model._meta.app_label}.{self.model._meta.model_name}_{self.name}"


class ChoiceSearchField(StrField):
    def __init__(self, model=None, name=None, nullable=None):
        super().__init__(model, name, nullable, suggest_options=True)

    def get_options(self, search):
        result = []
        choices = self._field_choices()
        if choices:
            search = search.lower()
            for c in choices:
                choice = str(c[0])
                if search in choice.lower():
                    result.append(choice)
        return result


class DjangoQLSchema:
    include = ()  # models to include into introspection
    exclude = ()  # models to exclude from introspection
    suggest_options = None

    def __init__(self, model):
        if not inspect.isclass(model) or not issubclass(model, models.Model):
            raise DjangoQLSchemaError(
                "Schema must be initialized with a subclass of Django model",
            )
        if self.include and self.exclude:
            raise DjangoQLSchemaError(
                "Either include or exclude can be specified, but not both",
            )
        if self.excluded(model):
            raise DjangoQLSchemaError(
                f"{model} can't be used with {self.__class__} because it's excluded from it",
            )
        self.current_model = model
        self._models = None
        if self.suggest_options is None:
            self.suggest_options = {}

    def excluded(self, model):
        return model in self.exclude or (self.include and model not in self.include)

    @property
    def models(self):
        if not self._models:
            self._models = self.introspect(
                model=self.current_model,
                exclude=tuple(self.model_label(m) for m in self.exclude),
            )
        return self._models

    @classmethod
    def model_label(self, model):
        return str(model._meta)

    def introspect(self, model, exclude=()):
        """
        Start with given model and recursively walk through its relationships.

        Returns a dict with all model labels and their fields found.
        """
        result = {}
        open_set = deque([model])
        closed_set = set(exclude)

        while open_set:
            model = open_set.popleft()
            model_label = self.model_label(model)

            if model_label in closed_set:
                continue

            model_fields = OrderedDict()
            for field in self.get_fields(model):
                if not isinstance(field, DjangoQLField):
                    field = self.get_field_instance(model, field)
                if not field:
                    continue
                if isinstance(field, RelationField):
                    open_set.append(field.related_model)
                model_fields[field.name] = field

            result[model_label] = model_fields
            closed_set.add(model_label)

        return result

    def get_fields(self, model):
        """
        By default, returns all field names of a given model.

        Override this method to limit field options. You can either return a
        plain list of field names from it, like ['id', 'name'], or call
        .super() and exclude unwanted fields from its result.
        """
        return sorted(
            [f.name for f in model._meta.get_fields() if f.name != "password"],
        )

    def get_field_instance(self, model, field_name):
        field = model._meta.get_field(field_name)
        field_kwargs = {"model": model, "name": field.name}
        if field.is_relation:
            if not field.related_model:
                # GenericForeignKey
                return
            if self.excluded(field.related_model):
                return
            field_cls = RelationField
            field_kwargs["related_model"] = field.related_model
        else:
            field_cls = self.get_field_cls(field)
        if isinstance(field, ManyToOneRel | ManyToManyRel | ForeignObjectRel):
            # Django 1.8 doesn't have .null attribute for these fields
            field_kwargs["nullable"] = True
        else:
            field_kwargs["nullable"] = field.null
        field_kwargs["suggest_options"] = field.name in self.suggest_options.get(model, [])
        return field_cls(**field_kwargs)

    def get_field_cls(self, field):
        str_fields = (
            models.CharField,
            models.TextField,
            models.UUIDField,
            models.BinaryField,
            models.GenericIPAddressField,
        )
        if isinstance(field, str_fields):
            return StrField
        elif isinstance(field, models.AutoField | models.IntegerField):
            return IntField
        elif isinstance(field, models.BooleanField | models.NullBooleanField):
            return BoolField
        elif isinstance(field, models.DecimalField | models.FloatField):
            return FloatField
        elif isinstance(field, models.DateTimeField):
            return DateTimeField
        elif isinstance(field, models.DateField):
            return DateField
        return DjangoQLField

    def as_dict(self):
        from akql.serializers import DjangoQLSchemaSerializer

        warnings.warn(
            "DjangoQLSchema.as_dict() is deprecated and will be removed in "
            "future releases. Please use DjangoQLSchemaSerializer instead.",
            stacklevel=2,
        )
        return DjangoQLSchemaSerializer().serialize(self)

    def resolve_name(self, name):
        assert isinstance(name, Name)
        model = self.model_label(self.current_model)
        field = None
        for name_part in name.parts:
            field = self.models[model].get(name_part)
            if not field:
                raise DjangoQLSchemaError(
                    "Unknown field: {}. Possible choices are: {}".format(
                        name_part,
                        ", ".join(sorted(self.models[model].keys())),
                    ),
                )
            if field.type == "relation":
                model = field.relation
                field = None
        return field

    def validate(self, node):
        """
        Validate DjangoQL AST tree vs. current schema
        """
        assert isinstance(node, Node)
        if isinstance(node.operator, Logical):
            self.validate(node.left)
            self.validate(node.right)
            return
        assert isinstance(node.left, Name)
        assert isinstance(node.operator, Comparison)
        assert isinstance(node.right, Const | List)

        # Check that field and value types are compatible
        field = self.resolve_name(node.left)
        value = node.right.value
        if field is None:
            if value is not None:
                raise DjangoQLSchemaError(
                    f"Related model {node.left.value} can be compared to None only, but not to "
                    f"{type(value).__name__}",
                )
        else:
            values = value if isinstance(node.right, List) else [value]
            for v in values:
                field.validate(v)
