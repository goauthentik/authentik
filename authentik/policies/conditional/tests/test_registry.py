"""Conditional policy registry tests"""

from django.test import TestCase

from authentik.policies.conditional.operators import OPERATORS
from authentik.policies.conditional.registry import registry
from authentik.policies.conditional.types import T, TypeKind, ValueType


class TestRegistry(TestCase):
    """Ensure everything registered by apps is consistent"""

    def test_scenarios(self):
        """Scenarios are complete, and every variable and setter is available in one"""
        facts = set()
        for scenario in registry.scenarios.values():
            with self.subTest(scenario=scenario.key):
                self.assertTrue(scenario.label)
                self.assertTrue(scenario.models)
                facts |= scenario.facts
        for item in [*registry.variables.values(), *registry.setters.values()]:
            with self.subTest(item=item.key):
                self.assertTrue(item.requires & facts)
                self.assertIsNotNone(item.app)

    def test_variables_usable(self):
        """Every variable can be used with at least one operator"""
        for variable in registry.variables.values():
            with self.subTest(variable=variable.key):
                if variable.type.kind != TypeKind.ANY:
                    self.assertTrue(
                        any(variable.type.kind in op.kinds for op in OPERATORS.values())
                    )
                if variable.type.kind == TypeKind.ENUM:
                    self.assertTrue(variable.type.choices)
                if variable.type.kind == TypeKind.LIST:
                    self.assertIsNotNone(variable.type.item)

    def test_operators(self):
        """Operand types can be computed for every operator and kind"""
        types = {
            **{kind: ValueType(kind) for kind in TypeKind},
            TypeKind.LIST: T.list(T.STRING),
        }
        for operator in OPERATORS.values():
            for kind in operator.kinds:
                with self.subTest(operator=operator.name, kind=kind):
                    operator.operand_type(types[kind])
