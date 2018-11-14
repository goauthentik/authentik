"""Generic models"""
from uuid import uuid4

from django.db import models


class CreatedUpdatedModel(models.Model):
    """Base Abstract Model to save created and update"""
    created = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model which uses a UUID as primary key"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    class Meta:
        abstract = True
