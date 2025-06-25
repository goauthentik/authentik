from django.urls import path

from authentik.tasks.api.tasks import TaskViewSet
from authentik.tasks.api.workers import WorkerView

api_urlpatterns = [
    ("tasks/tasks", TaskViewSet),
    path("tasks/workers", WorkerView.as_view(), name="tasks_workers"),
]
