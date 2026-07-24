from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.core.models import Application, User
from authentik.lib.models import ExpiringModel


class Persona(ExpiringModel, User):

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personas")
    primary_app = models.ForeignKey(Application, on_delete=models.CASCADE)

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Persona")
        verbose_name_plural = _("Personas")

    def __str__(self):
        return f"Persona {self.username} for {self.owner_id}"
