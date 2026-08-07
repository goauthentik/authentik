from django.apps import apps
from django.contrib.auth.models import Group as DjangoGroup
from django.db.models import ManyToManyField
from django.test import TestCase


class TestManyToMany(TestCase):
    def test_all_many_to_many_relations_are_explicit(self):
        implicit_m2ms = []
        exceptions = [DjangoGroup]

        for model in apps.get_models():
            if model in exceptions:
                continue
            for field in model._meta.get_fields():
                if not isinstance(field, ManyToManyField):
                    continue
                if field.remote_field.through._meta.auto_created:
                    implicit_m2ms.append(f"{model.__name__}.{field.name}")

        self.assertEqual(implicit_m2ms, [])
