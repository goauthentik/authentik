from django.db import models
from django_q.models import Task


class TaskStatus(models.TextChoices):
    UNKNOWN = "unknown"
    SUCCESSFUL = "successful"
    WARNING = "warning"
    ERROR = "error"


class TaskExtra(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="extra")
    uid = models.TextField(blank=True)
    soft_status = models.TextField(default=TaskStatus.UNKNOWN, choices=TaskStatus.choices)
    messages = models.JSONField(default=list)
    description = models.TextField(blank=True)

    def __str__(self):
        return str(self.task_id)
