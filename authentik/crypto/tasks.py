"""Crypto tasks"""

from glob import glob
from pathlib import Path
from sys import platform

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.base import load_pem_x509_certificate
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from dramatiq.middleware import Middleware
from structlog.stdlib import get_logger
from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from authentik.crypto.models import CertificateKeyPair
from authentik.lib.config import CONFIG
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.schedules.models import Schedule
from authentik.tenants.models import Tenant

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


class CertificateWatcherMiddleware(Middleware):
    """Middleware to start certificate file watcher"""

    def start_certificate_watcher(self):
        """Start certificate file watcher"""
        observer = Observer()
        kwargs = {}
        if platform.startswith("linux"):
            kwargs["event_filter"] = (FileCreatedEvent, FileModifiedEvent)
        observer.schedule(
            CertificateEventHandler(),
            CONFIG.get("cert_discovery_dir"),
            recursive=True,
            **kwargs,
        )
        observer.start()

    def after_worker_boot(self, broker, worker):
        if not settings.TEST:
            self.start_certificate_watcher()


class CertificateEventHandler(FileSystemEventHandler):
    """Event handler for certificate file events"""

    # We only ever get creation and modification events.
    # See the creation of the Observer instance above for the event filtering.

    # Even though we filter to only get file events, we might still get
    # directory events as some implementations such as inotify do not support
    # filtering on file/directory.

    def dispatch(self, event: FileSystemEvent) -> None:
        """Call specific event handler method. Ignores directory changes."""
        if event.is_directory:
            return None
        return super().dispatch(event)

    def on_created(self, event: FileSystemEvent):
        """Process certificate file creation"""
        LOGGER.debug(
            "Certificate file created, triggering discovery",
            file=event.src_path,
        )
        for tenant in Tenant.objects.filter(ready=True):
            with tenant:
                Schedule.dispatch_by_actor(certificate_discovery)

    def on_modified(self, event: FileSystemEvent):
        """Process certificate file modification"""
        LOGGER.debug(
            "Certificate file modified, triggering discovery",
            file=event.src_path,
        )
        for tenant in Tenant.objects.filter(ready=True):
            with tenant:
                Schedule.dispatch_by_actor(certificate_discovery)


@actor(description=_("Discover, import and update certificates from the filesystem."))
def certificate_discovery():
    self = CurrentTask.get_task()
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
            with open(path, encoding="utf-8") as _file:
                body = _file.read()
                if "PRIVATE KEY" in body:
                    private_keys[cert_name] = ensure_private_key_valid(body)
                else:
                    certs[cert_name] = ensure_certificate_valid(body)
            discovered += 1
        except (OSError, ValueError) as exc:
            LOGGER.warning("Failed to open file or invalid format", exc=exc, file=path)
    for name, cert_data in certs.items():
        # First, try to find by filename-based managed field
        cert = CertificateKeyPair.objects.filter(managed=MANAGED_DISCOVERED % name).first()

        # If not found by filename and we have a private key, check for existing key match
        if not cert and name in private_keys:
            existing_with_key = (
                CertificateKeyPair.objects.filter(
                    managed__startswith="goauthentik.io/crypto/discovered/",
                    key_data=private_keys[name],
                )
                .exclude(key_data="")
                .first()
            )
            if existing_with_key:
                cert = existing_with_key
                # Update name and managed field to reflect the new filename
                if cert.name != name:
                    cert.name = name
                    cert.managed = MANAGED_DISCOVERED % name
                    cert.save()

        # Create new certificate if not found
        if not cert:
            cert = CertificateKeyPair(
                name=name,
                managed=MANAGED_DISCOVERED % name,
            )

        # Update certificate data if changed
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
    self.info(f"Successfully imported {discovered} files.")
