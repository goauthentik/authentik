"""Crypto tasks"""
from glob import glob
from pathlib import Path

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


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task
def certificate_discovery(self: MonitoredTask):
    """Discover and update certificates form the filesystem"""
    certs = {}
    private_keys = {}
    discovered = 0
    for file in glob(CONFIG.y("cert_discovery_dir") + "/**", recursive=True):
        path = Path(file)
        if not path.exists():
            continue
        if path.is_dir():
            continue
        # Support certbot's directory structure
        if path.name in ["fullchain.pem", "privkey.pem"]:
            cert_name = path.parent.name
        else:
            cert_name = path.name.replace(path.suffix, "")
        try:
            with open(path, "r+", encoding="utf-8") as _file:
                body = _file.read()
                if "BEGIN RSA PRIVATE KEY" in body:
                    private_keys[cert_name] = body
                else:
                    certs[cert_name] = body
        except OSError as exc:
            LOGGER.warning("Failed to open file", exc=exc, file=path)
        discovered += 1
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
            if cert.key_data == private_keys[name]:
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
