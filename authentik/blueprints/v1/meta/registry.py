"""Base models"""
from django.apps import apps
from django.db.models import Model
from rest_framework.serializers import Serializer


class BaseMetaModel(Model):
    """Base models"""

    @staticmethod
    def serializer() -> Serializer:
        """Serializer similar to SerializerModel, but as a static method since
        this is an abstract model"""
        raise NotImplementedError

    class Meta:
        abstract = True


class MetaResult:
    """Result returned by Meta Models' serializers. Empty class but we can't return none as
    the framework doesn't allow that"""


class MetaModelRegistry:
    """Registry for pseudo meta models"""

    models: dict[str, BaseMetaModel]
    virtual_prefix: str

    def __init__(self, prefix: str) -> None:
        self.models = {}
        self.virtual_prefix = prefix

    def register(self, model_id: str):
        """Register model class under `model_id`"""

        def inner_wrapper(cls):
            self.models[model_id] = cls
            return cls

        return inner_wrapper

    def get_models(self):
        """Wrapper for django's `get_models` to list all models"""
        models = apps.get_models()
        for _, value in self.models.items():
            models.append(value)
        return models

    def get_model(self, app_label: str, model_id: str) -> type[Model]:
        """Get model checks if any virtual models are registered, and falls back
        to actual django models"""
        if app_label.lower() == self.virtual_prefix:
            if model_id.lower() in self.models:
                return self.models[model_id]
        return apps.get_model(app_label, model_id)


registry = MetaModelRegistry("authentik_blueprints")
