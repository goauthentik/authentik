"""Base models"""
from typing import Optional

from django.apps import apps
from django.db.models import Model


class BaseMetaModel:
    """Base models"""


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

    def get_model(self, app_label: str, model_id: str) -> Optional[type[Model]]:
        """Get model checks if any virtual models are registered, and falls back
        to actual django models"""
        if app_label == self.virtual_prefix:
            if model_id in self.models:
                return self.models[model_id]
        return apps.get_model(app_label, model_id)


registry = MetaModelRegistry("authentik_blueprints")
