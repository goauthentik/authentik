from authentik.tasks.schedules.api import ScheduleViewSet

api_urlpatterns = [
    ("tasks/schedules", ScheduleViewSet),
]
