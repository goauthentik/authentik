"""Docker SSH helper"""

import os
from pathlib import Path
from tempfile import gettempdir

from docker.errors import DockerException

from authentik.crypto.models import CertificateKeyPair

HEADER = "### Managed by authentik"
FOOTER = "### End Managed by authentik"


def opener(path: Path | str, flags: int):
    """File opener to create files as 600 perms"""
    return os.open(path, flags, 0o600)


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
                    "    StrictHostKeyChecking No\n",
                    "    UserKnownHostsFile /dev/null\n",
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

    def _without_own_blocks(self, lines: list[str]) -> list[str]:
        """Drop every config block written for this host, including the blank line after
        it, and keep all other lines"""
        kept = []
        in_block = False
        after_block = False
        for line in lines:
            if line == self.header:
                in_block = True
            elif in_block:
                if line == f"{FOOTER}\n" or line.startswith(HEADER):
                    in_block = False
                    after_block = line == f"{FOOTER}\n"
                    if not after_block:
                        kept.append(line)
            elif after_block and line == "\n":
                after_block = False
            else:
                after_block = False
                kept.append(line)
        return kept

    def cleanup(self):
        """Cleanup when we're done"""
        # The key path only depends on the keypair, so a parallel connection with the same
        # keypair may already have removed it; that must not skip the config cleanup
        try:
            os.unlink(self.key_path)
        except OSError:
            pass
        try:
            lines = self.config_path.read_text(encoding="utf-8").splitlines(keepends=True)
            with open(self.config_path, "w", encoding="utf-8") as ssh_config:
                ssh_config.writelines(self._without_own_blocks(lines))
        except OSError:
            # If we fail deleting a file it doesn't matter that much
            # since we're just in a container
            pass
