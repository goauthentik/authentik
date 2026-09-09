"""Tests for inheritance helpers."""

from contextlib import contextmanager

from django.db import connection, models
from django.test import TransactionTestCase
from django.test.utils import isolate_apps

from authentik.lib.utils.inheritance import get_deepest_child


@contextmanager
def temporary_inheritance_models():
    """Create a temporary multi-table inheritance graph for testing."""
    with isolate_apps("authentik.lib.tests"):

        class GrandParent(models.Model):
            class Meta:
                app_label = "tests"

            def __str__(self) -> str:
                return f"GrandParent({self.pk})"

        class Parent(GrandParent):
            class Meta:
                app_label = "tests"

            def __str__(self) -> str:
                return f"Parent({self.pk})"

        class Child(Parent):
            class Meta:
                app_label = "tests"

            def __str__(self) -> str:
                return f"Child({self.pk})"

        class GrandChild(Child):
            class Meta:
                app_label = "tests"

            def __str__(self) -> str:
                return f"GrandChild({self.pk})"

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(GrandParent)
            schema_editor.create_model(Parent)
            schema_editor.create_model(Child)
            schema_editor.create_model(GrandChild)

        try:
            yield GrandParent, Parent, Child, GrandChild
        finally:
            with connection.schema_editor() as schema_editor:
                schema_editor.delete_model(GrandChild)
                schema_editor.delete_model(Child)
                schema_editor.delete_model(Parent)
                schema_editor.delete_model(GrandParent)


class TestInheritanceUtils(TransactionTestCase):
    """Tests for helper functions in authentik.lib.utils.inheritance."""

    def test_get_deepest_child_grandparent_to_parent(self):
        """GrandParent -> Parent."""
        with temporary_inheritance_models() as (GrandParent, Parent, _Child, _GrandChild):
            parent = Parent.objects.create()
            grandparent = GrandParent.objects.get(pk=parent.pk)

            resolved = get_deepest_child(grandparent)

            self.assertIsInstance(resolved, Parent)
            self.assertEqual(resolved.pk, parent.pk)

    def test_get_deepest_child_grandparent_to_child(self):
        """GrandParent -> Child."""
        with temporary_inheritance_models() as (GrandParent, _Parent, Child, _GrandChild):
            child = Child.objects.create()
            grandparent = GrandParent.objects.get(pk=child.pk)

            resolved = get_deepest_child(grandparent)

            self.assertIsInstance(resolved, Child)
            self.assertEqual(resolved.pk, child.pk)

    def test_get_deepest_child_grandparent_to_grandchild(self):
        """GrandParent -> GrandChild."""
        with temporary_inheritance_models() as (GrandParent, _Parent, _Child, GrandChild):
            grandchild = GrandChild.objects.create()
            grandparent = GrandParent.objects.get(pk=grandchild.pk)

            resolved = get_deepest_child(grandparent)

            self.assertIsInstance(resolved, GrandChild)
            self.assertEqual(resolved.pk, grandchild.pk)

    def test_get_deepest_child_parent_to_child(self):
        """Parent -> Child (start from non-root)."""
        with temporary_inheritance_models() as (_GrandParent, Parent, Child, _GrandChild):
            child = Child.objects.create()
            parent = Parent.objects.get(pk=child.pk)

            resolved = get_deepest_child(parent)

            self.assertIsInstance(resolved, Child)
            self.assertEqual(resolved.pk, child.pk)

    def test_get_deepest_child_no_queries_with_preloaded_relations(self):
        """No extra queries when the inheritance chain is fully select_related."""
        with temporary_inheritance_models() as (GrandParent, _Parent, _Child, GrandChild):
            grandchild = GrandChild.objects.create()
            grandparent = GrandParent.objects.select_related("parent__child__grandchild").get(
                pk=grandchild.pk
            )

            with self.assertNumQueries(0):
                resolved = get_deepest_child(grandparent)

            self.assertIsInstance(resolved, GrandChild)
