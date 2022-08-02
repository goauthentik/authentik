"""v1 blueprints tasks"""
from dataclasses import asdict, dataclass, field
from glob import glob
from hashlib import sha512
from pathlib import Path
from typing import Optional

from dacite import from_dict
from django.db import DatabaseError, InternalError, ProgrammingError
from yaml import load

from authentik.blueprints.models import BlueprintInstance, BlueprintInstanceStatus
from authentik.blueprints.v1.common import BlueprintLoader, BlueprintMetadata
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.labels import LABEL_AUTHENTIK_EXAMPLE
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
@prefill_task
def blueprints_find() -> list[dict]:
    """Find blueprints and return valid ones"""
    blueprints = []
    for file in glob(f"{CONFIG.y('blueprints_dir')}/**/*.yaml", recursive=True):
        path = Path(file)
        with open(path, "r", encoding="utf-8") as blueprint_file:
            raw_blueprint = load(blueprint_file.read(), BlueprintLoader)
            metadata = raw_blueprint.get("metadata", None)
            version = raw_blueprint.get("version", 1)
            if version != 1:
                return
            blueprint_file.seek(0)
        file_hash = sha512(path.read_bytes()).hexdigest()
        blueprint = BlueprintFile(str(path), version, file_hash, path.stat().st_mtime)
        blueprint.meta = from_dict(BlueprintMetadata, metadata) if metadata else None
        blueprints.append(blueprint)
    return blueprints


@CELERY_APP.task(
    throws=(DatabaseError, ProgrammingError, InternalError),
)
@prefill_task
def blueprints_discover():
    """Find blueprints and check if they need to be created in the database"""
    for blueprint in blueprints_find():
        if (
            blueprint.meta
            and blueprint.meta.labels.get(LABEL_AUTHENTIK_EXAMPLE, "").lower() == "true"
        ):
            continue
        check_blueprint_v1_file(blueprint)


def check_blueprint_v1_file(blueprint: BlueprintFile):
    """Check if blueprint should be imported"""
    rel_path = Path(blueprint.path).relative_to(Path(CONFIG.y("blueprints_dir")))
    instance: BlueprintInstance = BlueprintInstance.objects.filter(path=blueprint.path).first()
    if not instance:
        instance = BlueprintInstance(
            name=blueprint.meta.name if blueprint.meta else str(rel_path),
            path=blueprint.path,
            context={},
            status=BlueprintInstanceStatus.UNKNOWN,
            enabled=True,
            managed_models=[],
            metadata=asdict(blueprint.meta),
        )
        instance.save()
    blueprint.meta = asdict(blueprint.meta)
    if instance.last_applied_hash != blueprint.hash:
        apply_blueprint.delay(instance.pk.hex)
        instance.last_applied_hash = blueprint.hash
        instance.save()


@CELERY_APP.task(
    bind=True,
    base=MonitoredTask,
)
def apply_blueprint(self: MonitoredTask, instance_pk: str):
    """Apply single blueprint"""
    self.save_on_success = False
    try:
        instance: BlueprintInstance = BlueprintInstance.objects.filter(pk=instance_pk).first()
        if not instance or not instance.enabled:
            return
        with open(instance.path, "r", encoding="utf-8") as blueprint_file:
            importer = Importer(blueprint_file.read())
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
            instance.status = BlueprintInstanceStatus.SUCCESSFUL
            instance.save()
    except (DatabaseError, ProgrammingError, InternalError, IOError) as exc:
        instance.status = BlueprintInstanceStatus.ERROR
        instance.save()
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
