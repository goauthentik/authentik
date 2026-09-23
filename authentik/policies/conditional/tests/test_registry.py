"""Conditional policy registry tests"""

from django.test import TestCase

from authentik.policies.conditional.operators import OPERATORS, operators_for
from authentik.policies.conditional.registry import DEFAULT_TARGET_FACTS, registry
from authentik.policies.conditional.types import TypeKind


class TestRegistry(TestCase):
    """Ensure everything registered by apps is consistent"""

    def test_facts(self):
        """Variables and targets only reference registered facts"""
        facts = set(registry.facts)
        self.assertTrue(DEFAULT_TARGET_FACTS <= facts)
        for variable in registry.variables.values():
            with self.subTest(variable=variable.key):
                self.assertTrue(variable.requires, "Variable must require at least one fact")
                self.assertTrue(variable.requires <= facts, variable.requires - facts)
        for target, target_facts in registry.targets.items():
            with self.subTest(target=target):
                self.assertTrue(target_facts <= facts, target_facts - facts)

    def test_variables_usable(self):
        """Every variable can be used with at least one operator, and is available somewhere"""
        all_target_facts = [DEFAULT_TARGET_FACTS, *registry.targets.values()]
        for variable in registry.variables.values():
            with self.subTest(variable=variable.key):
                self.assertTrue(any(variable.available_for(f) for f in all_target_facts))
                if variable.type.kind != TypeKind.ANY:
                    self.assertTrue(operators_for(variable.type))
                if variable.type.kind == TypeKind.ENUM:
                    self.assertTrue(variable.type.choices)
                if variable.type.kind == TypeKind.LIST:
                    self.assertIsNotNone(variable.type.item)

    def test_operators(self):
        """Operand types can be computed for every operator and kind"""
        for operator in OPERATORS.values():
            for kind in operator.kinds:
                with self.subTest(operator=operator.name, kind=kind):
                    operator.operand_type(
                        next(v.type for v in registry.variables.values() if v.type.kind == kind)
                    )
