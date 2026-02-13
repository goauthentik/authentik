from django.db import models

from authentik.admin.files.validation import validate_file_name


class FileField(models.TextField):
    default_validators = [validate_file_name]
