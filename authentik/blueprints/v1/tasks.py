"""v1 blueprints tasks"""
from dataclasses import asdict, dataclass, field
from hashlib import sha512
from pathlib import Path
from typing import Optional

from dacite import from_dict
from django.db import DatabaseError, InternalError, ProgrammingError
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from yaml import load
from yaml.error import YAMLError

from authentik.blueprints.models import BlueprintInstance, BlueprintInstanceStatus
from authentik.blueprints.v1.common import BlueprintLoader, BlueprintMetadata
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.labels import LABEL_AUTHENTIK_INSTANTIATE
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.lib.config import CONFIG
from authentik.root.celery import CELERY_APP


@dataclass
class BlueprintFile:
    """Basic info about a blueprint file"""

    path: str
    version: int
    hash: str
    last_m: int
    meta: Optional[BlueprintMetadata] = field(default=None)


@CELERY_APP.task(
    throws=(DatabaseError, ProgrammingError, InternalError),
)
def blueprints_find():
    """Find blueprints and return valid ones"""
    blueprints = []
    root = Path(CONFIG.y("blueprints_dir"))
    for file in root.glob("**/*.yaml"):
        path = Path(file)
        with open(path, "r", encoding="utf-8") as blueprint_file:
            try:
                raw_blueprint = load(blueprint_file.read(), BlueprintLoader)
            except YAMLError:
                raw_blueprint = None
            if not raw_blueprint:
                continue
            metadata = raw_blueprint.get("metadata", None)
            version = raw_blueprint.get("version", 1)
            if version != 1:
                continue
        file_hash = sha512(path.read_bytes()).hexdigest()
        blueprint = BlueprintFile(path.relative_to(root), version, file_hash, path.stat().st_mtime)
        blueprint.meta = from_dict(BlueprintMetadata, metadata) if metadata else None
        blueprints.append(blueprint)
    return blueprints


@CELERY_APP.task(
    throws=(DatabaseError, ProgrammingError, InternalError), base=MonitoredTask, bind=True
)
@prefill_task
def blueprints_discover(self: MonitoredTask):
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
        instance.metadata = asdict(blueprint.meta) if blueprint.meta else {}
        instance.save()
        apply_blueprint.delay(instance.pk.hex)


@CELERY_APP.task(
    bind=True,
    base=MonitoredTask,
)
def apply_blueprint(self: MonitoredTask, instance_pk: str):
    """Apply single blueprint"""
    self.set_uid(instance_pk)
    self.save_on_success = False
    try:
        instance: BlueprintInstance = BlueprintInstance.objects.filter(pk=instance_pk).first()
        if not instance or not instance.enabled:
            return
        full_path = Path(CONFIG.y("blueprints_dir")).joinpath(Path(instance.path))
        file_hash = sha512(full_path.read_bytes()).hexdigest()
        with open(full_path, "r", encoding="utf-8") as blueprint_file:
            importer = Importer(blueprint_file.read(), instance.context)
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
        instance.save()
        self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL))
    except (DatabaseError, ProgrammingError, InternalError, IOError) as exc:
        instance.status = BlueprintInstanceStatus.ERROR
        instance.save()
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
