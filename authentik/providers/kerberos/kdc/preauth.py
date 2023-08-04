from typing import Self

from authentik.providers.kerberos.kdc import checks, kdcreqhandler
from authentik.providers.kerberos.lib.exceptions import KerberosError


class PaBase(checks.Check):
    PA_TYPE: int

    def build_padata(self) -> tuple[int, bytes()]:
        return (self.PA_TYPE.value, bytes())

    def get_padata_values(self):
        self.padata_values = []
        for padata_type, padata_value in self.parent.request.get("padata", []):
            if padata_type == self.PA_TYPE.value:
                self.padata_values.append(padata_value)

    def check(self) -> bool:
        self.get_padata_values()
        if len(self.padata_values) > 1:
            raise KerberosError(
                code=KerberosError.Code.KDC_ERR_PADATA_TYPE_NOSUPP,
                message=f"Mutiple PA-DATA of type {self.PATADATA_TYPE}",
            )
        if len(self.padata_values) == 0:
            return False
        return True
