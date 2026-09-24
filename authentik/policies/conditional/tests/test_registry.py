"""Conditional policy registry tests"""

from django.test import TestCase

from authentik.policies.conditional.operators import OPERATORS, operators_for
from authentik.policies.conditional.registry import DEFAULT_TARGET_FACTS, registry
from authentik.policies.conditional.types import TypeKind


class TestRegistry(TestCase):
    """Ensure everything registered by apps is consistent"""

    def test_facts(self):
        """Variables, setters and scenarios only reference registered facts"""
        facts = set(registry.facts)
        self.assertLessEqual(DEFAULT_TARGET_FACTS, facts)
        for variable in registry.variables.values():
            with self.subTest(variable=variable.key):
                self.assertTrue(variable.requires, "Variable must require at least one fact")
                self.assertTrue(variable.requires <= facts, variable.requires - facts)
        for setter in registry.setters.values():
            with self.subTest(setter=setter.key):
                self.assertTrue(setter.requires <= facts, setter.requires - facts)
        for scenario in registry.scenarios.values():
            with self.subTest(scenario=scenario.key):
                self.assertTrue(scenario.facts <= facts, scenario.facts - facts)
                self.assertTrue(scenario.label)
                self.assertTrue(scenario.models, "Scenario must be used by at least one model")

    def test_variables_usable(self):
        """Every variable can be used with at least one operator, and is available in a
        scenario"""
        all_target_facts = [scenario.facts for scenario in registry.scenarios.values()]
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
