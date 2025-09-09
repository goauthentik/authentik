from enum import Enum

from pydantic import BaseModel


class UNSUPPORTED(BaseModel):
    pass


class OSFamily(Enum):

    linux = "linux"
    unix = "unix"
    bsd = "bsd"
    windows = "windows"
    macOS = "mac_os"
    android = "android"
    iOS = "i_os"
    other = "other"


class CommonDeviceData(BaseModel):
    class Disk(BaseModel):
        encryption: bool

    class OperatingSystem(BaseModel):
        firewall_enabled: bool
        family: OSFamily
        name: str
        version: str

    class Network(BaseModel):
        hostname: str
        dns_servers: list[str]

    class Hardware(BaseModel):
        model: str
        manufacturer: str

    class Software(BaseModel):
        name: str
        version: str

    os: OperatingSystem | UNSUPPORTED
    disks: list[Disk] | UNSUPPORTED
    network: Network | UNSUPPORTED
    hardware: Hardware | UNSUPPORTED
    software: list[Software] | UNSUPPORTED
