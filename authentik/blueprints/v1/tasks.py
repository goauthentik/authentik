"""v1 blueprints tasks"""
from dataclasses import asdict, dataclass, field
from hashlib import sha512
from pathlib import Path
from typing import Optional

from dacite.core import from_dict
from django.db import DatabaseError, InternalError, ProgrammingError
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
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
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.labels import LABEL_AUTHENTIK_INSTANTIATE
from authentik.blueprints.v1.oci import OCI_PREFIX
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.events.utils import sanitize_dict
from authentik.lib.config import CONFIG
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()
_file_watcher_started = False


@dataclass
class BlueprintFile:
    """Basic info about a blueprint file"""

    path: str
    version: int
    hash: str
    last_m: int
    meta: Optional[BlueprintMetadata] = field(default=None)


def start_blueprint_watcher():
    """Start blueprint watcher, if it's not running already."""
    # This function might be called twice since it's called on celery startup
    # pylint: disable=global-statement
    global _file_watcher_started
    if _file_watcher_started:
        return
    observer = Observer()
    observer.schedule(BlueprintEventHandler(), CONFIG.y("blueprints_dir"), recursive=True)
    observer.start()
    _file_watcher_started = True


class BlueprintEventHandler(FileSystemEventHandler):
    """Event handler for blueprint events"""

    def on_any_event(self, event: FileSystemEvent):
        if not isinstance(event, (FileCreatedEvent, FileModifiedEvent)):
            return
        if event.is_directory:
            return
        if isinstance(event, FileCreatedEvent):
            LOGGER.debug("new blueprint file created, starting discovery")
            blueprints_discovery.delay()
        if isinstance(event, FileModifiedEvent):
            path = Path(event.src_path)
            root = Path(CONFIG.y("blueprints_dir")).absolute()
            rel_path = str(path.relative_to(root))
            for instance in BlueprintInstance.objects.filter(path=rel_path):
                LOGGER.debug("modified blueprint file, starting apply", instance=instance)
                apply_blueprint.delay(instance.pk.hex)


@CELERY_APP.task(
    throws=(DatabaseError, ProgrammingError, InternalError),
)
def blueprints_find_dict():
    """Find blueprints as `blueprints_find` does, but return a safe dict"""
    blueprints = []
    for blueprint in blueprints_find():
        blueprints.append(sanitize_dict(asdict(blueprint)))
    return blueprints


def blueprints_find():
    """Find blueprints and return valid ones"""
    blueprints = []
    root = Path(CONFIG.y("blueprints_dir"))
    for path in root.rglob("**/*.yaml"):
        # Check if any part in the path starts with a dot and assume a hidden file
        if any(part for part in path.parts if part.startswith(".")):
            continue
        LOGGER.debug("found blueprint", path=str(path))
        with open(path, "r", encoding="utf-8") as blueprint_file:
            try:
                raw_blueprint = load(blueprint_file.read(), BlueprintLoader)
            except YAMLError as exc:
                raw_blueprint = None
                LOGGER.warning("failed to parse blueprint", exc=exc, path=str(path))
            if not raw_blueprint:
                continue
            metadata = raw_blueprint.get("metadata", None)
            version = raw_blueprint.get("version", 1)
            if version != 1:
                LOGGER.warning("invalid blueprint version", version=version, path=str(path))
                continue
        file_hash = sha512(path.read_bytes()).hexdigest()
        blueprint = BlueprintFile(
            str(path.relative_to(root)), version, file_hash, int(path.stat().st_mtime)
        )
        blueprint.meta = from_dict(BlueprintMetadata, metadata) if metadata else None
        blueprints.append(blueprint)
        LOGGER.debug(
            "parsed & loaded blueprint",
            hash=file_hash,
            path=str(path),
        )
    return blueprints


@CELERY_APP.task(
    throws=(DatabaseError, ProgrammingError, InternalError), base=MonitoredTask, bind=True
)
@prefill_task
def blueprints_discovery(self: MonitoredTask):
    """Find blueprints and check if they need to be created in the database"""
    count = 0
    for blueprint in blueprints_find():
        check_blueprint_v1_file(blueprint)
        count += 1
    self.set_status(
        TaskResult(
            TaskResultStatus.SUCCESSFUL,
            messages=[_("Successfully imported %(count)d files." % {"count": count})],
        )
    )


def check_blueprint_v1_file(blueprint: BlueprintFile):
    """Check if blueprint should be imported"""
    instance: BlueprintInstance = BlueprintInstance.objects.filter(path=blueprint.path).first()
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
    if instance.last_applied_hash != blueprint.hash:
        apply_blueprint.delay(str(instance.pk))


@CELERY_APP.task(
    bind=True,
    base=MonitoredTask,
)
def apply_blueprint(self: MonitoredTask, instance_pk: str):
    """Apply single blueprint"""
    self.save_on_success = False
    instance: Optional[BlueprintInstance] = None
    try:
        instance: BlueprintInstance = BlueprintInstance.objects.filter(pk=instance_pk).first()
        if not instance or not instance.enabled:
            return
        self.set_uid(slugify(instance.name))
        blueprint_content = instance.retrieve()
        file_hash = sha512(blueprint_content.encode()).hexdigest()
        importer = Importer(blueprint_content, instance.context)
        if importer.blueprint.metadata:
            instance.metadata = asdict(importer.blueprint.metadata)
        valid, logs = importer.validate()
        if not valid:
            instance.status = BlueprintInstanceStatus.ERROR
            instance.save()
            self.set_status(TaskResult(TaskResultStatus.ERROR, [x["event"] for x in logs]))
            return
        applied = importer.apply()
        if not applied:
            instance.status = BlueprintInstanceStatus.ERROR
            instance.save()
            self.set_status(TaskResult(TaskResultStatus.ERROR, "Failed to apply"))
            return
        instance.status = BlueprintInstanceStatus.SUCCESSFUL
        instance.last_applied_hash = file_hash
        instance.last_applied = now()
        self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL))
    except (
        DatabaseError,
        ProgrammingError,
        InternalError,
        IOError,
        BlueprintRetrievalFailed,
        EntryInvalidError,
    ) as exc:
        if instance:
            instance.status = BlueprintInstanceStatus.ERROR
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
    finally:
        if instance:
            instance.save()


@CELERY_APP.task()
def clear_failed_blueprints():
    """Remove blueprints which couldn't be fetched"""
    # Exclude OCI blueprints as those might be temporarily unavailable
    for blueprint in BlueprintInstance.objects.exclude(path__startswith=OCI_PREFIX):
        try:
            blueprint.retrieve()
        except BlueprintRetrievalFailed:
            blueprint.delete()
