"""Docker SSH helper"""
import os
from pathlib import Path
from tempfile import gettempdir

from docker.errors import DockerException

from authentik.crypto.models import CertificateKeyPair

SSH_CONFIG_DIR = Path("/etc/ssh/ssh_config.d/")


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

    def __init__(self, host: str, keypair: CertificateKeyPair) -> None:
        self.host = host
        self.keypair = keypair
        self.config_path = SSH_CONFIG_DIR / Path(self.host + ".conf")
        if not open(self.config_path, "w").writable():
            # SSH Config file already exists and there's no header from us, meaning that it's
            # been externally mapped into the container for more complex configs
            raise SSHManagedExternallyException(
                "SSH Config exists and does not contain authentik header"
            )
        if not self.keypair:
            raise DockerException("keypair must be set for SSH connections")

    def write_config(self, key_path: str):
        """Update the local user's ssh config file"""
        with open(self.config_path, "w", encoding="utf-8") as ssh_config:
            ssh_config.writelines(
                [
                    f"Host {self.host}\n",
                    f"    IdentityFile {str(key_path)}\n",
                    "    StrictHostKeyChecking No\n",
                    "    UserKnownHostsFile /dev/null\n",
                    "\n",
                ]
            )

    def write_key(self) -> Path:
        """Write keypair's private key to a temporary file"""
        path = Path(gettempdir(), f"{self.keypair.pk}_private.pem")
        with open(path, "w", encoding="utf8", opener=opener) as _file:
            _file.write(self.keypair.key_data)
        return path

    def write(self):
        """Write keyfile and update ssh config"""
        self.key_path = self.write_key()
        try:
            self.write_config(self.key_path)
        except OSError:
            self.cleanup()

    def cleanup(self):
        """Cleanup when we're done"""
        try:
            os.unlink(self.key_path)
            os.unlink(self.config_path)
        except OSError:
            # If we fail deleting a file it doesn't matter that much
            # since we're just in a container
            pass
