"""Docker SSH helper"""
import os
from pathlib import Path
from tempfile import gettempdir

from docker.errors import DockerException

from authentik.crypto.models import CertificateKeyPair

HEADER = "### Managed by authentik"
FOOTER = "### End Managed by authentik"


def opener(path, flags):
    """File opener to create files as 700 perms"""
    return os.open(path, flags, 0o700)


class SSHManagedExternallyException(DockerException):
    """Raised when the ssh config file is managed externally."""


class DockerInlineSSH:
    """Create paramiko ssh config from CertificateKeyPair"""

    host: str
    keypair: CertificateKeyPair

    key_path: str
    config_path: Path
    header: str

    def __init__(self, host: str, keypair: CertificateKeyPair) -> None:
        self.host = host
        self.keypair = keypair
        self.config_path = Path("~/.ssh/config").expanduser()
        if self.config_path.exists() and HEADER not in self.config_path.read_text(encoding="utf-8"):
            # SSH Config file already exists and there's no header from us, meaning that it's
            # been externally mapped into the container for more complex configs
            raise SSHManagedExternallyException(
                "SSH Config exists and does not contain authentik header"
            )
        if not self.keypair:
            raise DockerException("keypair must be set for SSH connections")
        self.header = f"{HEADER} - {self.host}\n"

    def write_config(self, key_path: str) -> bool:
        """Update the local user's ssh config file"""
        with open(self.config_path, "a+", encoding="utf-8") as ssh_config:
            if self.header in ssh_config.readlines():
                return False
            ssh_config.writelines(
                [
                    self.header,
                    f"Host {self.host}\n",
                    f"    IdentityFile {key_path}\n",
                    f"{FOOTER}\n",
                    "\n",
                ]
            )
        return True

    def write_key(self):
        """Write keypair's private key to a temporary file"""
        path = Path(gettempdir(), f"{self.keypair.pk}_private.pem")
        with open(path, "w", encoding="utf8", opener=opener) as _file:
            _file.write(self.keypair.key_data)
        return str(path)

    def write(self):
        """Write keyfile and update ssh config"""
        self.key_path = self.write_key()
        was_written = self.write_config(self.key_path)
        if not was_written:
            self.cleanup()

    def cleanup(self):
        """Cleanup when we're done"""
        try:
            os.unlink(self.key_path)
            with open(self.config_path, "r+", encoding="utf-8") as ssh_config:
                start = 0
                end = 0
                lines = ssh_config.readlines()
                for idx, line in enumerate(lines):
                    if line == self.header:
                        start = idx
                    if start != 0 and line == f"{FOOTER}\n":
                        end = idx
            with open(self.config_path, "w+", encoding="utf-8") as ssh_config:
                lines = lines[:start] + lines[end + 2 :]
                ssh_config.writelines(lines)
        except OSError:
            # If we fail deleting a file it doesn't matter that much
            # since we're just in a container
            pass
