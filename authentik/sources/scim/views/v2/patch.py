from copy import deepcopy

from deepmerge import always_merger
from scim2_filter_parser.attr_paths import AttrPath
from structlog.stdlib import get_logger

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
        self.logger = get_logger().bind()
        self.working_data = deepcopy(self._connection.attributes)

    def apply(self) -> dict:
        for op in self._ops:
            self.handle_single_op(op)
        return self.working_data

    def handle_single_op(self, op: PatchOperation):
        if not op.path:
            if not isinstance(op.value, dict):
                self.logger.warning("Failed to apply patch op")
                return
            always_merger.merge(self.working_data, op.value)
            return
        attr_path = AttrPath(f'{op.path} eq ""', {})
        ctx_wk: dict = self.working_data
        path_elements = [x for x in attr_path.first_path if x]
        if len(path_elements) < 1:
            return
        for path_part in path_elements[:-1]:
            ctx_wk.setdefault(path_part, {})
            ctx_wk = ctx_wk[path_part]
        last_path_element = path_elements[-1]
        if op.op == PatchOp.add:
            if last_path_element in ctx_wk and isinstance(ctx_wk[last_path_element], list):
                ctx_wk[last_path_element].extend(op.value)
            else:
                ctx_wk[last_path_element] = op.value
        elif op.op == PatchOp.replace:
            ctx_wk[last_path_element] = op.value
        elif op.op == PatchOp.remove:
            ctx_wk.pop(last_path_element, None)
