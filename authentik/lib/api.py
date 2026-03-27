from django.apps.registry import apps
from django.db.models import TextChoices
from django.utils.encoding import force_str

from authentik.blueprints.v1.importer import is_model_allowed
from authentik.blueprints.v1.meta.registry import BaseMetaModel


def app_choices() -> TextChoices:
    """Get a list of all installed applications that create events.
    Returns a list of tuples containing (dotted.app.path, name)"""
    choices = {}
    for app in apps.get_app_configs():
        if app.label.startswith("authentik"):
            choices[app.name] = (app.name, force_str(app.verbose_name))
    return TextChoices("Apps", choices)


def model_choices() -> TextChoices:
    """Get a list of all installed models
    Returns a list of tuples containing (dotted.model.path, name)"""
    choices = {}
    for model in apps.get_models():
        if not is_model_allowed(model) or issubclass(model, BaseMetaModel):
            continue
        name = f"{model._meta.app_label}.{model._meta.model_name}"
        choices[name] = (name, force_str(model._meta.verbose_name))
    return TextChoices("Models", choices)


Apps = app_choices()
Models = model_choices()
