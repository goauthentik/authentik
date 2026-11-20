"""v1 blueprints tasks"""

from dataclasses import asdict, dataclass, field
from datetime import timedelta
from pathlib import Path
from sys import platform
from typing import Any
from uuid import UUID

import pglock
from dacite.core import from_dict
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, DatabaseError, InternalError, ProgrammingError, connection
from django.utils.text import slugify
from django.utils.timezone import now
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
from yaml import load
from yaml.error import YAMLError

from authentik.blueprints.models import (
    BlueprintInstance,
    BlueprintInstanceStatus,
    BlueprintRetrievalFailed,
)
from authentik.blueprints.v1.common import BlueprintLoader, BlueprintMetadata, EntryInvalidError
from authentik.blueprints.v1.hash import blueprint_hash
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.labels import LABEL_AUTHENTIK_INSTANTIATE
from authentik.blueprints.v1.oci import OCI_PREFIX
from authentik.events.logs import capture_logs
from authentik.events.utils import sanitize_dict
from authentik.lib.config import CONFIG, advisory_lock_db_alias, postgresql_direct_db_enabled
from authentik.lib.utils.time import timedelta_from_string
from authentik.tasks.apps import PRIORITY_HIGH
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.schedules.models import Schedule

LOGGER = get_logger()


@dataclass
class BlueprintFile:
    """Basic info about a blueprint file"""

    path: str
    version: int
    hash: str
    last_m: int
    meta: BlueprintMetadata | None = field(default=None)


class BlueprintWatcherMiddleware(Middleware):
    def start_blueprint_watcher(self):
        """Start blueprint watcher"""
        observer = Observer()
        kwargs = {}
        if platform.startswith("linux"):
            kwargs["event_filter"] = (FileCreatedEvent, FileModifiedEvent)
        observer.schedule(
            BlueprintEventHandler(), CONFIG.get("blueprints_dir"), recursive=True, **kwargs
        )
        observer.start()

    def after_worker_boot(self, broker, worker):
        if not settings.TEST:
            self.start_blueprint_watcher()


class BlueprintEventHandler(FileSystemEventHandler):
    """Event handler for blueprint events"""

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
        """Process file creation"""
        LOGGER.debug("new blueprint file created, starting discovery")
        Schedule.dispatch_by_actor(blueprints_discovery)

    def on_modified(self, event: FileSystemEvent):
        """Process file modification"""
        path = Path(event.src_path)
        root = Path(CONFIG.get("blueprints_dir")).absolute()
        rel_path = str(path.relative_to(root))
        for instance in BlueprintInstance.objects.filter(path=rel_path, enabled=True):
            LOGGER.debug("modified blueprint file, starting apply", instance=instance)
            # A single change can raise several events, and the same change is seen by
            # every worker's watcher, so only apply if the content changed
            apply_blueprint.send_with_options(
                args=(instance.pk,), kwargs={"only_if_changed": True}, rel_obj=instance
            )


@actor(
    description=_("Find blueprints as `blueprints_find` does, but return a safe dict."),
    priority=PRIORITY_HIGH,
)
def blueprints_find_dict():
    blueprints = []
    for blueprint in blueprints_find():
        blueprints.append(sanitize_dict(asdict(blueprint)))
    return blueprints


def blueprints_find() -> list[BlueprintFile]:
    """Find blueprints and return valid ones"""
    blueprints = []
    root = Path(CONFIG.get("blueprints_dir"))
    for path in root.rglob("**/*.yaml"):
        rel_path = path.relative_to(root)
        # Check if any part in the path starts with a dot and assume a hidden file
        if any(part for part in rel_path.parts if part.startswith(".")):
            continue
        with open(path, encoding="utf-8") as blueprint_file:
            content = blueprint_file.read()
            try:
                raw_blueprint = load(content, BlueprintLoader)
            except YAMLError as exc:
                raw_blueprint = None
                LOGGER.warning("failed to parse blueprint", exc=exc, path=str(rel_path))
            if not raw_blueprint:
                continue
            metadata = raw_blueprint.get("metadata", None)
            version = raw_blueprint.get("version", 1)
            if version != 1:
                LOGGER.warning("invalid blueprint version", version=version, path=str(rel_path))
                continue
        file_hash = blueprint_hash(content)
        blueprint = BlueprintFile(str(rel_path), version, file_hash, int(path.stat().st_mtime))
        blueprint.meta = from_dict(BlueprintMetadata, metadata) if metadata else None
        blueprints.append(blueprint)
    return blueprints


# Largest value Postgres accepts for `lock_timeout`
MAX_LOCK_TIMEOUT = timedelta(milliseconds=2**31 - 1)


def _blueprint_lock_timeout() -> timedelta:
    """How long to wait for a blueprint lock.

    Waits for at most half the task time limit, so the wait times out before the time
    limit can interrupt the task while the lock is being granted, which would leave the
    lock held. Behind a transaction pooler without a direct connection, the lock and its
    timeout can land on different server connections, so do not wait at all there."""
    if CONFIG.get_bool("postgresql.use_pgbouncer", False) and not postgresql_direct_db_enabled():
        return timedelta(0)
    time_limit = timedelta_from_string(CONFIG.get("worker.task_default_time_limit"))
    return min(time_limit / 2, MAX_LOCK_TIMEOUT)


def _blueprint_lock(name: str) -> pglock.advisory:
    """Session-level advisory lock serializing blueprint work across worker threads and
    replicas. Waits instead of skipping where it can, as the holder may be working from
    content older than the change that triggered the waiting task. A task that gives up
    leaves the change to the next discovery."""
    return pglock.advisory(
        lock_id=f"goauthentik.io/{connection.schema_name}/blueprints/{name}",
        timeout=_blueprint_lock_timeout(),
        side_effect=pglock.Return,
        using=advisory_lock_db_alias(),
    )


@actor(description=_("Find blueprints and check if they need to be created in the database."))
def blueprints_discovery(path: str | None = None):
    self = CurrentTask.get_task()
    # Discovery runs on every process start, so on a fresh install several runs can
    # otherwise create the same instance at once
    with _blueprint_lock("discovery") as acquired:
        if not acquired:
            self.warning("Timed out waiting for another blueprint discovery to finish")
            return
        count = 0
        for blueprint in blueprints_find():
            if path and blueprint.path != path:
                continue
            check_blueprint_v1_file(blueprint)
            count += 1
    self.info(f"Successfully imported {count} files.")


def check_blueprint_v1_file(blueprint: BlueprintFile):
    """Check if blueprint should be imported"""
    # Read from the primary, so an instance created by a discovery that finished while
    # this one waited for the lock is not missed on a lagging replica
    instance: BlueprintInstance = (
        BlueprintInstance.objects.using(DEFAULT_DB_ALIAS).filter(path=blueprint.path).first()
    )
    if (
        blueprint.meta
        and blueprint.meta.labels.get(LABEL_AUTHENTIK_INSTANTIATE, "").lower() == "false"
    ):
        return
    if not instance:
        instance = BlueprintInstance(
            name=blueprint.meta.name if blueprint.meta else str(blueprint.path),
            path=blueprint.path,
            context={},
            status=BlueprintInstanceStatus.UNKNOWN,
            enabled=True,
            managed_models=[],
            metadata={},
        )
        instance.save()
        LOGGER.info(
            "Creating new blueprint instance from file", instance=instance, path=instance.path
        )
    if instance.last_applied_hash != blueprint.hash:
        LOGGER.info("Applying blueprint due to changed file", instance=instance, path=instance.path)
    elif instance.status == BlueprintInstanceStatus.ERROR:
        LOGGER.info("Retrying failed blueprint", instance=instance, path=instance.path)
    else:
        return
    apply_blueprint.send_with_options(
        args=(instance.pk,), kwargs={"only_if_changed": True}, rel_obj=instance
    )


def _save_result(instance: BlueprintInstance, status: BlueprintInstanceStatus, **fields: Any):
    """Write the outcome of an apply. Only the columns an apply owns are written, so this
    neither reverts changes made to the instance while the apply ran nor re-creates an
    instance deleted in the meantime, which a full `save()` would do."""
    instance.status = status
    for key, value in fields.items():
        setattr(instance, key, value)
    BlueprintInstance.objects.filter(pk=instance.pk).update(
        status=status, metadata=instance.metadata, last_updated=now(), **fields
    )


@actor(description=_("Apply single blueprint."))
def apply_blueprint(instance_pk: UUID, only_if_changed: bool = False):
    """Apply a blueprint instance. With `only_if_changed`, skip it if the current
    content was already applied successfully, which collapses duplicate requests."""
    self = CurrentTask.get_task()
    self.set_uid(str(instance_pk))
    # Concurrent applies of the same instance would create the same objects twice and
    # overwrite each other's result
    with _blueprint_lock(f"apply/{instance_pk}") as acquired:
        if not acquired:
            self.warning("Timed out waiting for another apply of this blueprint to finish")
            return
        _apply_blueprint(instance_pk, only_if_changed)


def _apply_blueprint(instance_pk: UUID, only_if_changed: bool):
    self = CurrentTask.get_task()
    # Read the instance only once the lock is held, and from the primary rather than a
    # possibly lagging replica, so it reflects any apply that finished while this one waited
    instance: BlueprintInstance | None = (
        BlueprintInstance.objects.using(DEFAULT_DB_ALIAS).filter(pk=instance_pk).first()
    )
    if not instance:
        self.warning(f"Could not find blueprint {instance_pk}, skipping")
        return
    self.set_uid(slugify(instance.name))
    if not instance.enabled:
        self.info(f"Blueprint {instance.name} is disabled, skipping")
        return
    try:
        blueprint_content = instance.retrieve()
        file_hash = blueprint_hash(blueprint_content)
        if (
            only_if_changed
            and instance.status == BlueprintInstanceStatus.SUCCESSFUL
            and instance.last_applied_hash == file_hash
        ):
            self.info(f"Blueprint {instance.name} is already applied, skipping")
            return
        importer = Importer.from_string(blueprint_content, instance.context)
        if importer.blueprint.metadata:
            instance.metadata = asdict(importer.blueprint.metadata)
        valid, logs = importer.validate()
        if not valid:
            _save_result(instance, BlueprintInstanceStatus.ERROR)
            self.logs(logs)
            return
        with capture_logs() as logs:
            applied = importer.apply()
            if not applied:
                _save_result(instance, BlueprintInstanceStatus.ERROR)
                self.logs(logs)
                return
        _save_result(
            instance,
            BlueprintInstanceStatus.SUCCESSFUL,
            last_applied_hash=file_hash,
            last_applied=now(),
        )
    except (
        OSError,
        DatabaseError,
        ProgrammingError,
        InternalError,
        BlueprintRetrievalFailed,
        EntryInvalidError,
    ) as exc:
        _save_result(instance, BlueprintInstanceStatus.ERROR)
        self.error(exc)


@actor(description=_("Remove blueprints which couldn't be fetched."))
def clear_failed_blueprints():
    # Exclude OCI blueprints as those might be temporarily unavailable
    for blueprint in BlueprintInstance.objects.exclude(path__startswith=OCI_PREFIX):
        try:
            blueprint.retrieve()
        except BlueprintRetrievalFailed:
            blueprint.delete()
