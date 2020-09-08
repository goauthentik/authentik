"""passbook API Helpers"""
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from model_utils.managers import InheritanceQuerySet
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField


class InheritancePrimaryKeyRelatedField(PrimaryKeyRelatedField):
    """rest_framework PrimaryKeyRelatedField which resolves
    model_manager's InheritanceQuerySet"""

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        if isinstance(queryset, InheritanceQuerySet):
            return queryset.select_subclasses()
        return queryset

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            queryset = self.get_queryset()
            if isinstance(queryset, InheritanceQuerySet):
                return queryset.get_subclass(pk=data)
            return queryset.get(pk=data)
        except ObjectDoesNotExist:
            self.fail("does_not_exist", pk_value=data)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)


class InheritanceModelSerializer(ModelSerializer):
    """rest_framework ModelSerializer which automatically uses InheritancePrimaryKeyRelatedField
    for every primary key"""

    serializer_related_field = InheritancePrimaryKeyRelatedField
