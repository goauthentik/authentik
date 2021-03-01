"""Utility Widgets"""
from itertools import groupby

from django.forms.models import ModelChoiceField, ModelChoiceIterator


class GroupedModelChoiceIterator(ModelChoiceIterator):
    """ModelChoiceField which groups objects by their verbose_name"""

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset.order_by("name")
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        # We can't use DB-level sorting as we sort by subclass
        queryset = sorted(queryset, key=lambda x: x._meta.verbose_name)
        for group, objs in groupby(queryset, key=lambda x: x._meta.verbose_name):
            yield (group, [self.choice(obj) for obj in objs])


class GroupedModelChoiceField(ModelChoiceField):
    """ModelChoiceField which groups objects by their verbose_name"""

    iterator = GroupedModelChoiceIterator
