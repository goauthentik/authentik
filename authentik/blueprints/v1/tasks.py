"""v1 blueprints tasks"""
from glob import glob
from hashlib import sha512
from pathlib import Path
from re import I

from django.db import DatabaseError, InternalError, ProgrammingError
from yaml import safe_load

from authentik.blueprints.models import BlueprintInstance, BlueprintInstanceStatus
from authentik.blueprints.v1.importer import Importer
from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.lib.config import CONFIG
from authentik.root.celery import CELERY_APP


@CELERY_APP.task()
def blueprints_v1_discover():
    """Find blueprints and check if they need to be created in the database"""
    for folder in CONFIG.y("blueprint_locations"):
        for file in glob(f"{folder}/**.yaml", recursive=True):
            check_blueprint_v1_file(Path(file))


def check_blueprint_v1_file(path: Path):
    """Check if blueprint should be imported"""
    with open(path, "r", encoding="utf-8") as blueprint_file:
        raw_blueprint = safe_load(blueprint_file.read())
        version = raw_blueprint.get("version", 1)
        if version != 1:
            return
        blueprint_file.seek(0)
        hash = sha512(blueprint_file.read()).hexdigest()
    instance: BlueprintInstance = BlueprintInstance.objects.filter(path=path).first()
    if not instance:
        instance = BlueprintInstance(
            name=path.name,
            path=str(path),
            context={},
            status=BlueprintInstanceStatus.UNKNOWN,
            enabled=True,
            managed_models="",
        )
        instance.save()
    if instance.last_applied_hash != hash:
        apply_blueprint.delay(instance.pk.hex)
        instance.last_applied_hash = hash
        instance.save()


@CELERY_APP.task(
    bind=True,
    base=MonitoredTask,
)
def apply_blueprint(self: MonitoredTask, instance_pk: str):
    """Apply single blueprint"""
    try:
        instance: BlueprintInstance = BlueprintInstance.objects.filter(pk=instance_pk)
        if not instance:
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
    except (DatabaseError, ProgrammingError, InternalError) as exc:
        instance.status = BlueprintInstanceStatus.ERROR
        instance.save()
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
