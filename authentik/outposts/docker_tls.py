"""Create Docker TLSConfig from CertificateKeyPair"""

import os
from pathlib import Path
from tempfile import gettempdir

from docker.tls import TLSConfig

from authentik.crypto.models import CertificateKeyPair


def opener(path, flags):
    """File opener to create files as 600 perms"""
    return os.open(path, flags, 0o600)


class DockerInlineTLS:
    """Create Docker TLSConfig from CertificateKeyPair"""

    verification_kp: CertificateKeyPair | None
    authentication_kp: CertificateKeyPair | None

    _paths: list[str]

    def __init__(
        self,
        verification_kp: CertificateKeyPair | None,
        authentication_kp: CertificateKeyPair | None,
    ) -> None:
        self.verification_kp = verification_kp
        self.authentication_kp = authentication_kp
        self._paths = []

    def write_file(self, name: str, contents: str) -> str:
        """Wrapper for mkstemp that uses fdopen"""
        path = Path(gettempdir(), name)
        with open(path, "w", encoding="utf8", opener=opener) as _file:
            _file.write(contents)
        self._paths.append(str(path))
        return str(path)

    def cleanup(self):
        """Clean up certificates when we're done"""
        for path in self._paths:
            os.unlink(path)

    def write(self) -> TLSConfig:
        """Create TLSConfig with Certificate Key pairs"""
        # So yes, this is quite ugly. But sadly, there is no clean way to pass
        # docker-py (which is using requests (which is using urllib3)) a certificate
        # for verification or authentication as string.
        # Because we run in docker, and our tmpfs is isolated to us, we can just
        # write out the certificates and keys to files and use their paths
        config_args = {}
        if self.verification_kp:
            ca_cert_path = self.write_file(
                f"{self.verification_kp.pk.hex}-cert.pem",
                self.verification_kp.certificate_data,
            )
            config_args["ca_cert"] = ca_cert_path
        if self.authentication_kp:
            auth_cert_path = self.write_file(
                f"{self.authentication_kp.pk.hex}-cert.pem",
                self.authentication_kp.certificate_data,
            )
            auth_key_path = self.write_file(
                f"{self.authentication_kp.pk.hex}-key.pem",
                self.authentication_kp.key_data,
            )
            config_args["client_cert"] = (auth_cert_path, auth_key_path)
        return TLSConfig(**config_args)
