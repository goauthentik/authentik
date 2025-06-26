"""v1 blueprints tasks"""

from dataclasses import asdict, dataclass, field
from hashlib import sha512
from pathlib import Path
from sys import platform
from uuid import UUID

from dacite.core import from_dict
from django.conf import settings
from django.db import DatabaseError, InternalError, ProgrammingError
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask, CurrentTaskNotFound
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
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.labels import LABEL_AUTHENTIK_INSTANTIATE
from authentik.blueprints.v1.oci import OCI_PREFIX
from authentik.events.logs import capture_logs
from authentik.events.utils import sanitize_dict
from authentik.lib.config import CONFIG
from authentik.tasks.models import Task
from authentik.tasks.schedules.models import Schedule
from authentik.tenants.models import Tenant

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
        for tenant in Tenant.objects.filter(ready=True):
            with tenant:
                Schedule.dispatch_by_actor(blueprints_discovery)

    def on_modified(self, event: FileSystemEvent):
        """Process file modification"""
        path = Path(event.src_path)
        root = Path(CONFIG.get("blueprints_dir")).absolute()
        rel_path = str(path.relative_to(root))
        for tenant in Tenant.objects.filter(ready=True):
            with tenant:
                for instance in BlueprintInstance.objects.filter(path=rel_path, enabled=True):
                    LOGGER.debug("modified blueprint file, starting apply", instance=instance)
                    apply_blueprint.send_with_options(args=(instance.pk,), rel_obj=instance)


@actor(
    description=_("Find blueprints as `blueprints_find` does, but return a safe dict."),
    throws=(DatabaseError, ProgrammingError, InternalError),
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
        if any(part for part in path.parts if part.startswith(".")):
            continue
        with open(path, encoding="utf-8") as blueprint_file:
            try:
                raw_blueprint = load(blueprint_file.read(), BlueprintLoader)
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
        file_hash = sha512(path.read_bytes()).hexdigest()
        blueprint = BlueprintFile(str(rel_path), version, file_hash, int(path.stat().st_mtime))
        blueprint.meta = from_dict(BlueprintMetadata, metadata) if metadata else None
        blueprints.append(blueprint)
    return blueprints


@actor(
    description=_("Find blueprints and check if they need to be created in the database."),
    throws=(DatabaseError, ProgrammingError, InternalError),
)
def blueprints_discovery(path: str | None = None):
    self: Task = CurrentTask.get_task()
    count = 0
    for blueprint in blueprints_find():
        if path and blueprint.path != path:
            continue
        check_blueprint_v1_file(blueprint)
        count += 1
    self.info(f"Successfully imported {count} files.")


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
        LOGGER.info(
            "Creating new blueprint instance from file", instance=instance, path=instance.path
        )
    if instance.last_applied_hash != blueprint.hash:
        LOGGER.info("Applying blueprint due to changed file", instance=instance, path=instance.path)
        apply_blueprint.send_with_options(args=(instance.pk,), rel_obj=instance)


@actor(description=_("Apply single blueprint."))
def apply_blueprint(instance_pk: UUID):
    try:
        self: Task = CurrentTask.get_task()
    except CurrentTaskNotFound:
        self = Task()
    self.set_uid(str(instance_pk))
    instance: BlueprintInstance | None = None
    try:
        instance: BlueprintInstance = BlueprintInstance.objects.filter(pk=instance_pk).first()
        if not instance:
            self.warning(f"Could not find blueprint {instance_pk}, skipping")
            return
        self.set_uid(slugify(instance.name))
        if not instance.enabled:
            self.info(f"Blueprint {instance.name} is disabled, skipping")
            return
        blueprint_content = instance.retrieve()
        file_hash = sha512(blueprint_content.encode()).hexdigest()
        importer = Importer.from_string(blueprint_content, instance.context)
        if importer.blueprint.metadata:
            instance.metadata = asdict(importer.blueprint.metadata)
        valid, logs = importer.validate()
        if not valid:
            instance.status = BlueprintInstanceStatus.ERROR
            instance.save()
            self.logs(logs)
            return
        with capture_logs() as logs:
            applied = importer.apply()
            if not applied:
                instance.status = BlueprintInstanceStatus.ERROR
                instance.save()
                self.logs(logs)
                return
        instance.status = BlueprintInstanceStatus.SUCCESSFUL
        instance.last_applied_hash = file_hash
        instance.last_applied = now()
    except (
        OSError,
        DatabaseError,
        ProgrammingError,
        InternalError,
        BlueprintRetrievalFailed,
        EntryInvalidError,
    ) as exc:
        if instance:
            instance.status = BlueprintInstanceStatus.ERROR
        self.error(exc)
    finally:
        if instance:
            instance.save()


@actor(description=_("Remove blueprints which couldn't be fetched."))
def clear_failed_blueprints():
    # Exclude OCI blueprints as those might be temporarily unavailable
    for blueprint in BlueprintInstance.objects.exclude(path__startswith=OCI_PREFIX):
        try:
            blueprint.retrieve()
        except BlueprintRetrievalFailed:
            blueprint.delete()
