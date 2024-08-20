"""Generic models"""

import re

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Model
from django.utils.regex_helper import _lazy_re_compile
from guardian.models import UserObjectPermission
from model_utils.managers import InheritanceManager
from rest_framework.serializers import BaseSerializer


class SerializerModel(models.Model):
    """Base Abstract Model which has a serializer"""

    class Meta:
        abstract = True

    @property
    def serializer(self) -> type[BaseSerializer]:
        """Get serializer for this model"""
        # Special handling for built-in source
        if (
            hasattr(self, "managed")
            and hasattr(self, "MANAGED_INBUILT")
            and self.managed == self.MANAGED_INBUILT
        ):
            from authentik.core.api.sources import SourceSerializer

            return SourceSerializer
        raise NotImplementedError


class CreatedUpdatedModel(models.Model):
    """Base Abstract Model to save created and update"""

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InheritanceAutoManager(InheritanceManager):
    """Object manager which automatically selects the subclass"""

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class InheritanceForwardManyToOneDescriptor(models.fields.related.ForwardManyToOneDescriptor):
    """Forward ManyToOne Descriptor that selects subclass. Requires InheritanceAutoManager."""

    def get_queryset(self, **hints):
        return self.field.remote_field.model.objects.db_manager(hints=hints).select_subclasses()


class InheritanceForeignKey(models.ForeignKey):
    """Custom ForeignKey that uses InheritanceForwardManyToOneDescriptor"""

    forward_related_accessor_class = InheritanceForwardManyToOneDescriptor


class DomainlessURLValidator(URLValidator):
    """Subclass of URLValidator which doesn't check the domain
    (to allow hostnames without domain)"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.host_re = "(" + self.hostname_re + self.domain_re + "|localhost)"
        self.regex = _lazy_re_compile(
            r"^(?:[a-z0-9.+-]*)://"  # scheme is validated separately
            r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
            r"(?:" + self.ipv4_re + "|" + self.ipv6_re + "|" + self.host_re + ")"
            r"(?::\d{1,5})?"  # port
            r"(?:[/?#][^\s]*)?"  # resource path
            r"\Z",
            re.IGNORECASE,
        )
        self.schemes = ["http", "https", "blank"] + list(self.schemes)

    def __call__(self, value: str):
        # Check if the scheme is valid.
        scheme = value.split("://")[0].lower()
        if scheme not in self.schemes:
            value = "default" + value
        super().__call__(value)


class DomainlessFormattedURLValidator(DomainlessURLValidator):
    """URL validator which allows for python format strings"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.formatter_re = r"([%\(\)a-zA-Z])*"
        self.host_re = "(" + self.formatter_re + self.hostname_re + self.domain_re + "|localhost)"
        self.regex = _lazy_re_compile(
            r"^(?:[a-z0-9.+-]*)://"  # scheme is validated separately
            r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
            r"(?:" + self.ipv4_re + "|" + self.ipv6_re + "|" + self.host_re + ")"
            r"(?::\d{1,5})?"  # port
            r"(?:[/?#][^\s]*)?"  # resource path
            r"\Z",
            re.IGNORECASE,
        )
        self.schemes = ["http", "https", "blank"] + list(self.schemes)


__internal_models = []


def internal_model(cls):
    __internal_models.append(cls)
    return cls


def excluded_models() -> list[type[Model]]:
    """Return a list of all excluded models that shouldn't be exposed via API
    or other means (internal only, base classes, non-used objects, etc)"""

    from django.apps import apps
    from django.contrib.auth.models import Group as DjangoGroup
    from django.contrib.auth.models import User as DjangoUser

    static = [
        # Django only classes
        DjangoUser,
        DjangoGroup,
        ContentType,
        Permission,
        UserObjectPermission,
    ]
    return tuple(static + [x for x in apps.get_models() if x in __internal_models])
