from dataclasses import dataclass
from datetime import datetime

from authentik.lib.kerberos import iana
from authentik.lib.kerberos.principal import PrincipalName


def _to_bytes_with_length(s: str | bytes) -> bytes:
    return len(s).to_bytes(2, byteorder="big") + (s.encode() if isinstance(s, str) else s)


@dataclass
class EncryptionKey:
    key_type: iana.EncryptionType
    key: bytes

    def to_bytes(self) -> bytes:
        return self.key_type.value.to_bytes(2, byteorder="big") + _to_bytes_with_length(self.key)


@dataclass
class Principal:
    realm: str
    name: PrincipalName

    def to_bytes(self) -> bytes:
        result = len(self.name.name).to_bytes(2, byteorder="big") + _to_bytes_with_length(
            self.name.realm if self.name.realm is not None else self.realm
        )
        for name in self.name.name:
            result += _to_bytes_with_length(name)
        result += self.name.name_type.value.to_bytes(4, byteorder="big")
        return result


@dataclass
class KeytabEntry:
    principal: Principal
    timestamp: datetime
    kvno8: int
    key: EncryptionKey
    kvno: int | None = None

    def to_bytes(self) -> bytes:
        data = (
            self.principal.to_bytes()
            + int(self.timestamp.timestamp()).to_bytes(4, byteorder="big")
            + self.kvno8.to_bytes(1, byteorder="big")
            + self.key.to_bytes()
        )
        if self.kvno is None:
            self.kvno = self.kvno8
        data += self.kvno.to_bytes(4, byteorder="big")
        return len(data).to_bytes(4, byteorder="big") + data


@dataclass
class Keytab:
    entries: list[KeytabEntry]

    def to_bytes(self) -> bytes:
        result = 0x05.to_bytes(1, byteorder="big")  # Header, always 5
        result += 0x02.to_bytes(1, byteorder="big")  # Version, always 2
        for entry in self.entries:
            result += entry.to_bytes()
        return result
