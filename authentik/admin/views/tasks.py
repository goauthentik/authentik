"""authentik Tasks List"""
from typing import Any, Dict

from django.views.generic.base import TemplateView

from authentik.admin.mixins import AdminRequiredMixin
from authentik.events.monitored_tasks import TaskInfo, TaskResultStatus


class TaskListView(AdminRequiredMixin, TemplateView):
    """Show list of all background tasks"""

    template_name = "administration/task/list.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs["object_list"] = sorted(
            TaskInfo.all().values(), key=lambda x: x.task_name
        )
        kwargs["task_successful"] = TaskResultStatus.SUCCESSFUL
        kwargs["task_warning"] = TaskResultStatus.WARNING
        kwargs["task_error"] = TaskResultStatus.ERROR
        return kwargs
