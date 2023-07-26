from dataclasses import dataclass

from authentik.lib.kerberos import constants
from authentik.lib.kerberos.exceptions import KerberosException


@dataclass
class PrincipalName:
    name_type: constants.PrincipalNameType
    name: list[str]
    realm: str | None = None

    @classmethod
    def from_spn(cls, spn):
        name, realm, *_ = spn.rsplit("@", maxsplit=1) + [None]
        components = name.split("/")
        match len(components):
            case 0:
                raise KerberosException("Principal must have a principal")
            case 1:
                name_type = constants.PrincipalNameType.NT_SRV_INST
            case 2:
                name_type = constants.PrincipalNameType.NT_SRV_HST
            case _:
                name_type = constants.PrincipalNameType.NT_SRV_XHST
        return cls(
            name_type=name_type,
            name=components,
            realm=realm,
        )

