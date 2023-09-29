"""Expression tasks"""
from glob import glob
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from structlog.stdlib import get_logger
from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.lib.config import CONFIG
from authentik.policies.expression.models import MANAGED_DISCOVERED, ExpressionVariable
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()
_file_watcher_started = False


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task
def variable_discovery(self: MonitoredTask):
    """Discover, import and update variables from the filesystem"""
    variables = {}
    discovered = 0
    base_path = Path(CONFIG.get("variables_discovery_dir")).absolute()
    for file in glob(str(base_path) + "/**", recursive=True):
        path = Path(file)
        if not path.exists():
            continue
        if path.is_dir():
            continue
        try:
            with open(path, "r", encoding="utf-8") as _file:
                body = _file.read()
                variables[str(path.relative_to(base_path))] = body
            discovered += 1
        except (OSError, ValueError) as exc:
            LOGGER.warning("Failed to open file", exc=exc, file=path)
    for name, value in variables.items():
        variable = ExpressionVariable.objects.filter(managed=MANAGED_DISCOVERED % name).first()
        if not variable:
            variable = ExpressionVariable(name=name, managed=MANAGED_DISCOVERED % name)
        if variable.value != value:
            variable.value = value
            variable.save()
    self.set_status(
        TaskResult(
            TaskResultStatus.SUCCESSFUL,
            messages=[_("Successfully imported %(count)d files." % {"count": discovered})],
        )
    )


class VariableEventHandler(FileSystemEventHandler):
    """Event handler for variable events"""

    def on_any_event(self, event: FileSystemEvent):
        if not isinstance(event, (FileCreatedEvent, FileModifiedEvent)):
            return
        if event.is_directory:
            return
        LOGGER.debug("variable file changed, starting discovery", file=event.src_path)
        variable_discovery.delay()


def start_variables_watcher():
    """Start variables watcher, if it's not running already."""
    # This function might be called twice since it's called on celery startup
    # pylint: disable=global-statement
    global _file_watcher_started
    if _file_watcher_started:
        return
    observer = Observer()
    observer.schedule(VariableEventHandler(), CONFIG.get("variables_discovery_dir"), recursive=True)
    observer.start()
    _file_watcher_started = True
