from enum import Enum

from pydanticscim.responses import SCIMError as BaseSCIMError
from rest_framework.exceptions import ValidationError


class SCIMErrorTypes(Enum):
    invalid_filter = "invalidFilter"
    too_many = "tooMany"
    uniqueness = "uniqueness"
    mutability = "mutability"
    invalid_syntax = "invalidSyntax"
    invalid_path = "invalidPath"
    no_target = "noTarget"
    invalid_value = "invalidValue"
    invalid_vers = "invalidVers"
    sensitive = "sensitive"


class SCIMError(BaseSCIMError):
    scimType: SCIMErrorTypes | None = None
    detail: str | None = None


class SCIMValidationError(ValidationError):
    status_code = 400
    default_detail = SCIMError(scimType=SCIMErrorTypes.invalid_syntax, status=400)

    def __init__(self, detail: SCIMError | None):
        if detail is None:
            detail = self.default_detail
        detail.status = self.status_code
        self.detail = detail.model_dump(mode="json", exclude_none=True)


class SCIMConflictError(SCIMValidationError):
    status_code = 409

    def __init__(self, detail: str):
        super().__init__(
            SCIMError(
                detail=detail,
                scimType=SCIMErrorTypes.uniqueness,
                status=self.status_code,
            )
        )


class SCIMNotFoundError(SCIMValidationError):
    status_code = 404

    def __init__(self, detail: str):
        super().__init__(
            SCIMError(
                detail=detail,
                status=self.status_code,
            )
        )
