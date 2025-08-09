import re
from io import BytesIO
from tarfile import TarInfo, open

from django.db.models import Model
from django.db.models.fields import CharField, SlugField, TextField
from django.db.models.fields.json import JSONField

from authentik.blueprints.v1.exporter import Exporter
from authentik.core.models import User
from lifecycle.support import encrypt, generate

SENSITIVE_VALUE_PLACEHOLDER = "<REDACTED>"


class SupportExporter(Exporter):
    """Blueprint exporter which censors sensitive model attributes"""

    sensitive_fields = re.compile(
        # Partially taken from Django's SafeExceptionReporterFilter
        "API|AUTH|TOKEN|KEY|SECRET|PASS|SIGNATURE|CREDENTIALS",
        re.I,
    )

    def __init__(self):
        super().__init__()
        self.excluded_models.append(User)

    def alter_model(self, model: Model):
        for field in model._meta.fields:
            if not self.sensitive_fields.search(field.name):
                continue
            if isinstance(field, TextField | CharField | SlugField):
                setattr(model, field.name, SENSITIVE_VALUE_PLACEHOLDER)
            elif isinstance(field, JSONField):
                setattr(model, field.name, {})
        return model


def generate_support_bundle():
    fh = BytesIO()
    exporter = SupportExporter()
    files = {
        "authentik/support.jwe": encrypt(generate()),
        "authentik/blueprint.yaml": exporter.export_to_string(),
    }
    with open(fileobj=fh, mode="w:gz") as tar:
        for path, file in files.items():
            info = TarInfo(path)
            info.size = len(file)
            tar.addfile(info, BytesIO(file.encode()))
    final_data = fh.getvalue()
    return final_data
