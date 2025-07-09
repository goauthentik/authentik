from copy import copy

from scim2_filter_parser.attr_paths import AttrPath

from authentik.providers.scim.clients.schema import PatchOp, PatchOperation
from authentik.sources.scim.models import SCIMSourceGroup, SCIMSourceUser
from authentik.sources.scim.views.v2.exceptions import SCIMValidationError


class SCIMPatcher:
    """Apply a SCIM PATCH operation to an object by applying changes to the attributes we store"""

    def __init__(self, connection: SCIMSourceUser | SCIMSourceGroup, ops: list):
        self._connection = connection
        self._ops: list[PatchOperation] = []
        for _op in ops:
            operation = PatchOperation.model_validate(_op)
            if operation.op.lower() not in ["add", "remove", "replace"]:
                raise SCIMValidationError()
            self._ops.append(operation)

    def apply(self, ignored_path_prefixes: list[str] | None = None) -> dict:
        if not ignored_path_prefixes:
            ignored_path_prefixes = []
        working_data = copy(self._connection.attributes)
        for op in self._ops:
            attr_path = AttrPath(f'{op.path} eq ""', {})
            ctx_wk: dict = working_data
            path_elements = [x for x in attr_path.first_path if x]
            if path_elements[0] in ignored_path_prefixes:
                continue
            for path_part in path_elements[:-1]:
                ctx_wk.setdefault(path_part, {})
                ctx_wk = ctx_wk[path_part]
            last_path_element = path_elements[-1]
            if op.op in (PatchOp.add, PatchOp.replace):
                ctx_wk[last_path_element] = op.value
            elif op.op == PatchOp.remove:
                ctx_wk.pop(last_path_element, None)
        return working_data
