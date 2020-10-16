"""passbook Tasks List"""
from typing import Any, Dict

from django.core.cache import cache
from django.views.generic.base import TemplateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.lib.tasks import TaskResultStatus


class TaskListView(AdminRequiredMixin, TemplateView):
    """Show list of all background tasks"""

    template_name = "administration/task/list.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs["object_list"] = cache.get_many(cache.keys("task_*"))
        kwargs["task_successful"] = TaskResultStatus.SUCCESSFUL
        kwargs["task_warning"] = TaskResultStatus.WARNING
        kwargs["task_error"] = TaskResultStatus.ERROR
        return kwargs
