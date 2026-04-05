from django.test.testcases import TestCase
from drf_spectacular.generators import SchemaGenerator

from authentik.enterprise.reports.tests.utils import patch_license


@patch_license
class TestSchemaMatch(TestCase):
    def setUp(self) -> None:
        generator = SchemaGenerator()
        self.schema = generator.get_schema(request=None, public=True)

    def _index_params_by_name(self, parameters):
        result = {}
        for p in parameters or []:
            if p.get("in") != "query":
                continue
            schema = p.get("schema", {})
            result[p["name"]] = {
                "required": p.get("required", False),
                "type": schema.get("type"),
                "format": schema.get("format"),
                "enum": tuple(schema.get("enum", [])),
            }
        return result

    def _find_operation_by_operation_id(self, operation_id):
        for path_item in self.schema.get("paths", {}).values():
            for operation in path_item.values():
                if isinstance(operation, dict) and operation.get("operationId") == operation_id:
                    return operation
        raise AssertionError(f"operationId '{operation_id}' not found in schema")

    def _get_op_params(self, operation_id):
        operation = self._find_operation_by_operation_id(operation_id)
        return self._index_params_by_name(operation.get("parameters", []))

    def test_user_export_action_query_params_match_list(self):
        list_params = self._get_op_params("core_users_list")
        del list_params["include_groups"]  # Not applicable for export
        del list_params["include_roles"]  # Not applicable for export
        export_params = self._get_op_params("core_users_export_create")
        self.assertDictEqual(list_params, export_params)

    def test_event_export_action_query_params_match_list(self):
        list_params = self._get_op_params("events_events_list")
        export_params = self._get_op_params("events_events_export_create")
        self.assertDictEqual(list_params, export_params)
