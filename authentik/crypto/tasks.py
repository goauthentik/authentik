"""Crypto tasks"""
from glob import glob
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.base import load_pem_x509_certificate
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import get_logger

from authentik.crypto.models import CertificateKeyPair
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.lib.config import CONFIG
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()

MANAGED_DISCOVERED = "goauthentik.io/crypto/discovered/%s"


def ensure_private_key_valid(body: str):
    """Attempt loading of a PEM Private key without password"""
    load_pem_private_key(
        str.encode("\n".join([x.strip() for x in body.split("\n")])),
        password=None,
        backend=default_backend(),
    )
    return body


def ensure_certificate_valid(body: str):
    """Attempt loading of a PEM-encoded certificate"""
    load_pem_x509_certificate(body.encode("utf-8"), default_backend())
    return body


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task
def certificate_discovery(self: MonitoredTask):
    """Discover, import and update certificates from the filesystem"""
    certs = {}
    private_keys = {}
    discovered = 0
    for file in glob(CONFIG.get("cert_discovery_dir") + "/**", recursive=True):
        path = Path(file)
        if not path.exists():
            continue
        if path.is_dir():
            continue
        # For certbot setups, we want to ignore archive.
        if "archive" in file:
            continue
        # Support certbot's directory structure
        if path.name in ["fullchain.pem", "privkey.pem"]:
            cert_name = path.parent.name
        else:
            cert_name = path.name.replace(path.suffix, "")
        try:
            with open(path, "r", encoding="utf-8") as _file:
                body = _file.read()
                if "PRIVATE KEY" in body:
                    private_keys[cert_name] = ensure_private_key_valid(body)
                else:
                    certs[cert_name] = ensure_certificate_valid(body)
            discovered += 1
        except (OSError, ValueError) as exc:
            LOGGER.warning("Failed to open file or invalid format", exc=exc, file=path)
    for name, cert_data in certs.items():
        cert = CertificateKeyPair.objects.filter(managed=MANAGED_DISCOVERED % name).first()
        if not cert:
            cert = CertificateKeyPair(
                name=name,
                managed=MANAGED_DISCOVERED % name,
            )
        dirty = False
        if cert.certificate_data != cert_data:
            cert.certificate_data = cert_data
            dirty = True
        if name in private_keys:
            if cert.key_data != private_keys[name]:
                cert.key_data = private_keys[name]
                dirty = True
        if dirty:
            cert.save()
    self.set_status(
        TaskResult(
            TaskResultStatus.SUCCESSFUL,
            messages=[_("Successfully imported %(count)d files." % {"count": discovered})],
        )
    )
