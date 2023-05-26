from dataclasses import dataclass

from authentik.lib.kerberos import constants


@dataclass
class PrincipalName:
    name_type: constants.PrincipalNameType
    name: list[str]
    realm: str | None = None
