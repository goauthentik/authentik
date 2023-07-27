"""Kerberos keytab"""
from dataclasses import dataclass
from datetime import datetime
from typing import Self, Tuple

from authentik.lib.kerberos import iana
from authentik.lib.kerberos.exceptions import KerberosException
from authentik.lib.kerberos.principal import PrincipalName, PrincipalNameType


def _to_bytes_with_length(data: str | bytes, size: int = 2) -> bytes:
    return len(data).to_bytes(size, byteorder="big") + (
        data.encode() if isinstance(data, str) else data
    )


def _from_bytes_with_length(data: bytes, size: int = 2) -> Tuple[bytes, bytes]:
    length = int.from_bytes(data[:size], byteorder="big")
    return data[size : size + length], data[size + length :]


@dataclass
class EncryptionKey:
    """Kerberos keytab representation of an encryption key"""

    key_type: iana.EncryptionType
    key: bytes

    def to_bytes(self) -> bytes:
        """Export to bytes"""
        return self.key_type.value.to_bytes(2, byteorder="big") + _to_bytes_with_length(self.key)

    @classmethod
    def from_bytes(cls, data: bytes) -> (Self, bytes):
        """Import from bytes"""
        key_type = iana.EncryptionType(int.from_bytes(data[:2], byteorder="big"))
        key, remainder = _from_bytes_with_length(data[2:])
        return (
            cls(
                key_type=key_type,
                key=key,
            ),
            remainder,
        )


@dataclass
class Principal:
    """Kerberos keytab representation of a principal"""

    realm: str
    name: PrincipalName

    def to_bytes(self) -> bytes:
        """Export to bytes"""
        result = len(self.name.name).to_bytes(2, byteorder="big") + _to_bytes_with_length(
            self.name.realm if self.name.realm is not None else self.realm
        )
        for name in self.name.name:
            result += _to_bytes_with_length(name)
        result += self.name.name_type.value.to_bytes(4, byteorder="big")
        return result

    @classmethod
    def from_bytes(cls, data: bytes) -> (Self, bytes):
        """Import from bytes"""
        name_count = int.from_bytes(data[:2], byteorder="big")
        realm, remainder = _from_bytes_with_length(data[2:])
        realm = realm.decode()
        names = []
        for _ in range(name_count):
            name, remainder = _from_bytes_with_length(remainder)
            names.append(name.decode())
        name_type = int.from_bytes(remainder[:4], byteorder="big")
        return (
            cls(
                realm=realm,
                name=PrincipalName(
                    name=names,
                    name_type=PrincipalNameType(name_type),
                    realm=realm,
                ),
            ),
            remainder[4:],
        )


@dataclass
class KeytabEntry:
    """Kerberos keytab entry representation"""

    principal: Principal
    timestamp: datetime
    key: EncryptionKey
    kvno: int
    kvno8: int | None = None

    def to_bytes(self) -> bytes:
        """Export to bytes"""
        if self.kvno8 is None:
            self.kvno8 = self.kvno % 2**8
        data = (
            self.principal.to_bytes()
            + int(self.timestamp.timestamp()).to_bytes(4, byteorder="big")
            + self.kvno8.to_bytes(1, byteorder="big")
            + self.key.to_bytes()
        )
        data += self.kvno.to_bytes(4, byteorder="big")
        return len(data).to_bytes(4, byteorder="big") + data

    @classmethod
    def from_bytes(cls, data: bytes) -> (Self, bytes):
        """Import from bytes"""
        data, final_remainder = _from_bytes_with_length(data, size=4)
        principal, remainder = Principal.from_bytes(data)
        timestamp = datetime.fromtimestamp(int.from_bytes(remainder[:4], byteorder="big"))
        kvno8 = int.from_bytes(remainder[4:5], byteorder="big")
        key, remainder = EncryptionKey.from_bytes(remainder[5:])
        kvno = int.from_bytes(remainder[:4], byteorder="big")
        return (
            cls(
                principal=principal,
                timestamp=timestamp,
                key=key,
                kvno=kvno,
                kvno8=kvno8,
            ),
            final_remainder,
        )


@dataclass
class Keytab:
    """Kerberos keytab representation"""

    entries: list[KeytabEntry]

    def to_bytes(self) -> bytes:
        """Export to bytes"""
        result = 0x05.to_bytes(1, byteorder="big")  # Header, always 5
        result += 0x02.to_bytes(1, byteorder="big")  # Version, always 2
        for entry in self.entries:
            result += entry.to_bytes()
        return result

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Import from bytes"""
        header = data[0]
        version = data[1]
        if (header, version) != (0x05, 0x02):
            raise KerberosException("Unsupported keytab format")
        remainder = data[2:]
        entries = []
        while remainder:
            entry, remainder = KeytabEntry.from_bytes(remainder)
            entries.append(entry)
        return cls(entries=entries)
