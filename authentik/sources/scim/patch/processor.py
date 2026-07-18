from typing import Any

from authentik.providers.scim.clients.schema import PatchOp, PatchOperation
from authentik.sources.scim.constants import SCIM_URN_USER_ENTERPRISE
from authentik.sources.scim.patch.parser import SCIMPathParser


class SCIMPatchProcessor:
    """Processes SCIM patch operations on Python dictionaries"""

    def __init__(self):
        self.parser = SCIMPathParser()

    def apply_patches(self, data: dict[str, Any], patches: list[PatchOperation]) -> dict[str, Any]:
        """Apply a list of patch operations to the data"""
        result = data.copy()

        for _patch in patches:
            patch = PatchOperation.model_validate(_patch)
            if patch.path is None:
                # Handle operations with no path - value contains attribute paths as keys
                self._apply_bulk_operation(result, patch.op, patch.value)
            elif patch.op == PatchOp.add:
                self._apply_add(result, patch.path, patch.value)
            elif patch.op == PatchOp.remove:
                self._apply_remove(result, patch.path)
            elif patch.op == PatchOp.replace:
                self._apply_replace(result, patch.path, patch.value)

        return result

    def _apply_bulk_operation(
        self, data: dict[str, Any], operation: PatchOp, value: dict[str, Any]
    ):
        """Apply bulk operations when path is None"""
        if not isinstance(value, dict):
            return
        for path, val in value.items():
            if operation == PatchOp.add:
                self._apply_add(data, path, val)
            elif operation == PatchOp.remove:
                self._apply_remove(data, path)
            elif operation == PatchOp.replace:
                self._apply_replace(data, path, val)

    def _apply_add(self, data: dict[str, Any], path: str, value: Any):
        """Apply ADD operation"""
        components = self.parser.parse_path(path)

        if len(components) == 1 and not components[0]["filter"]:
            # Simple path
            attr = components[0]["attribute"]
            if components[0]["sub_attribute"]:
                if attr not in data:
                    data[attr] = {}
                # Somewhat hacky workaround for the manager attribute of the enterprise schema
                # ideally we'd do this based on the schema
                if attr == SCIM_URN_USER_ENTERPRISE and components[0]["sub_attribute"] == "manager":
                    data[attr][components[0]["sub_attribute"]] = {"value": value}
                else:
                    data[attr][components[0]["sub_attribute"]] = value
            elif attr in data:
                data[attr].append(value)
            else:
                data[attr] = value
        else:
            # Complex path with filters
            self._navigate_and_modify(data, components, value, "add")

    def _apply_remove(self, data: dict[str, Any], path: str):
        """Apply REMOVE operation"""
        components = self.parser.parse_path(path)

        if len(components) == 1 and not components[0]["filter"]:
            # Simple path
            attr = components[0]["attribute"]
            if components[0]["sub_attribute"]:
                if attr in data and isinstance(data[attr], dict):
                    data[attr].pop(components[0]["sub_attribute"], None)
            else:
                data.pop(attr, None)
        else:
            # Complex path with filters
            self._navigate_and_modify(data, components, None, "remove")

    def _apply_replace(self, data: dict[str, Any], path: str, value: Any):
        """Apply REPLACE operation"""
        components = self.parser.parse_path(path)

        if len(components) == 1 and not components[0]["filter"]:
            # Simple path
            attr = components[0]["attribute"]
            if components[0]["sub_attribute"]:
                if attr not in data:
                    data[attr] = {}
                # Somewhat hacky workaround for the manager attribute of the enterprise schema
                # ideally we'd do this based on the schema
                if attr == SCIM_URN_USER_ENTERPRISE and components[0]["sub_attribute"] == "manager":
                    data[attr][components[0]["sub_attribute"]] = {"value": value}
                else:
                    data[attr][components[0]["sub_attribute"]] = value
            else:
                data[attr] = value
        else:
            # Complex path with filters
            self._navigate_and_modify(data, components, value, "replace")

    def _navigate_and_modify(  # noqa PLR0912
        self, data: dict[str, Any], components: list[dict[str, Any]], value: Any, operation: str
    ):
        """Navigate through complex paths and apply modifications"""
        current = data

        for i, component in enumerate(components):
            attr = component["attribute"]
            filter_expr = component["filter"]
            sub_attr = component["sub_attribute"]

            if filter_expr:
                # Handle array with filter
                if attr not in current:
                    if operation == "add":
                        current[attr] = []
                    else:
                        return

                if not isinstance(current[attr], list):
                    return

                # Find matching items
                matching_items = []
                for item in current[attr]:
                    if self._matches_filter(item, filter_expr):
                        matching_items.append(item)

                if not matching_items and operation == "add":
                    # Create new item if none match (only for simple comparison filters)
                    if filter_expr.get("type", "comparison") == "comparison":
                        new_item = {filter_expr["attribute"]: filter_expr["value"]}
                        current[attr].append(new_item)
                        matching_items = [new_item]

                # Apply operation to matching items
                for item in matching_items:
                    if sub_attr:
                        if operation in {"add", "replace"}:
                            item[sub_attr] = value
                        elif operation == "remove":
                            item.pop(sub_attr, None)
                    elif operation in {"add", "replace"}:
                        if isinstance(value, dict):
                            item.update(value)
                        else:
                            # If value is not a dict, we can't merge it
                            pass
                    elif operation == "remove":
                        # Remove the entire item
                        if item in current[attr]:
                            current[attr].remove(item)
            # Handle simple attribute
            elif i == len(components) - 1:
                # Last component
                if sub_attr:
                    if attr not in current:
                        current[attr] = {}
                    if operation in {"add", "replace"}:
                        current[attr][sub_attr] = value
                    elif operation == "remove":
                        current[attr].pop(sub_attr, None)
                elif operation in {"add", "replace"}:
                    current[attr] = value
                elif operation == "remove":
                    current.pop(attr, None)
            else:
                # Navigate deeper
                if attr not in current:
                    current[attr] = {}
                current = current[attr]

    def _matches_filter(self, item: dict[str, Any], filter_expr: dict[str, Any]) -> bool:
        """Check if an item matches the filter expression"""
        if not filter_expr:
            return True

        filter_type = filter_expr.get("type", "comparison")

        if filter_type == "comparison":
            return self._matches_comparison(item, filter_expr)
        elif filter_type == "logical":
            return self._matches_logical(item, filter_expr)

        return False

    def _matches_comparison(  # noqa PLR0912
        self, item: dict[str, Any], filter_expr: dict[str, Any]
    ) -> bool:
        """Check if an item matches a comparison filter"""
        attr = filter_expr["attribute"]
        operator = filter_expr["operator"]
        expected_value = filter_expr["value"]

        if attr not in item:
            return False

        actual_value = item[attr]

        if operator == "eq":
            return actual_value == expected_value
        elif operator == "ne":
            return actual_value != expected_value
        elif operator == "co":
            return str(expected_value) in str(actual_value)
        elif operator == "sw":
            return str(actual_value).startswith(str(expected_value))
        elif operator == "ew":
            return str(actual_value).endswith(str(expected_value))
        elif operator == "gt":
            return actual_value > expected_value
        elif operator == "lt":
            return actual_value < expected_value
        elif operator == "ge":
            return actual_value >= expected_value
        elif operator == "le":
            return actual_value <= expected_value
        elif operator == "pr":
            return actual_value is not None

        return False

    def _matches_logical(self, item: dict[str, Any], filter_expr: dict[str, Any]) -> bool:
        """Check if an item matches a logical filter expression"""
        operator = filter_expr["operator"]

        if operator == "and":
            left_result = self._matches_filter(item, filter_expr["left"])
            right_result = self._matches_filter(item, filter_expr["right"])
            return left_result and right_result
        elif operator == "or":
            left_result = self._matches_filter(item, filter_expr["left"])
            right_result = self._matches_filter(item, filter_expr["right"])
            return left_result or right_result
        elif operator == "not":
            operand_result = self._matches_filter(item, filter_expr["operand"])
            return not operand_result

        return False
