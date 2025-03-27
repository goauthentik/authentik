from authentik.tasks.api import TaskViewSet

api_urlpatterns = [
    ("tasks/tasks", TaskViewSet),
]
