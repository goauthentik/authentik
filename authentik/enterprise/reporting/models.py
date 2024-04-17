from uuid import uuid4

from django.db import models


class Report(models.Model):

    report_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField()

    schedule = models.TextField()

    def __str__(self) -> str:
        return self.name

    def do_the_thing(self):
        pass
