"""Generic models"""

import re
from hashlib import sha256
from typing import Self

from django.core.validators import URLValidator
from django.db import models
from django.db.models import Manager, Q, QuerySet
from django.utils.regex_helper import _lazy_re_compile
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager
from rest_framework.serializers import BaseSerializer

from authentik.lib.utils.reflection import class_to_path


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


class DeprecatedMixin:
    """Mixin for classes that are deprecated"""


class InternallyManagedMixin:
    """Mixin for models that should _not_ be manageable via blueprint."""


class SimpleThroughModel(models.Model, InternallyManagedMixin):
    """
    Base class for explicit many-to-many through models, mainly used for adjusting API behavior as
    if there were no explicit through models
    """

    class Meta:
        abstract = True


# Upper bound for stored client identifiers. Identifiers of registered OAuth2 providers are
# much shorter, but other registration kinds may use URLs.
CLIENT_ID_MAX_LENGTH = 2048


def hash_client_id(client_id: str) -> str:
    """Fixed-length digest of a client identifier, used to index rows by client.
    The digest only narrows a lookup; the full client identifier must still be compared."""
    return sha256(client_id.encode("utf-8")).hexdigest()


class HashedClientIDModel(models.Model):
    """Records the exact identifier of a client, which may be too long to index, together
    with an indexable digest of it. Both are empty for rows that belong to no specific
    client. The digest is kept in sync on every save."""

    client_id = models.CharField(
        max_length=CLIENT_ID_MAX_LENGTH, null=True, default=None, verbose_name=_("Client ID")
    )
    client_id_hash = models.CharField(max_length=64, null=True, default=None, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.client_id_hash = hash_client_id(self.client_id) if self.client_id is not None else None
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "client_id" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"client_id_hash"}
        return super().save(*args, **kwargs)


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
        scheme = value.split("://", maxsplit=1)[0].lower()
        if scheme not in self.schemes:
            value = "default" + value
        super().__call__(value)


class DomainlessFormattedURLValidator(DomainlessURLValidator):
    """URL validator which allows for python format strings and paths relative to the
    current host. Browsers treat a leading `//` or `/\\` as another host, so those are rejected."""

    relative_re = _lazy_re_compile(r"^/(?![/\\])[^\s\\]*\Z")

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
        self.schemes = ["http", "https", "blank", "ssh", "sftp"] + list(self.schemes)

    def __call__(self, value: str):
        if self.relative_re.match(value):
            return
        super().__call__(value)


class ExpiringManager(Manager):
    """Manager for expiring objects which filters out expired objects by default"""

    def get_queryset(self):
        return QuerySet(self.model, using=self._db).exclude(expires__lt=now(), expiring=True)

    def including_expired(self):
        return QuerySet(self.model, using=self._db)


class ExpiringModel(models.Model):
    """Base Model which can expire, and is automatically cleaned up."""

    expires = models.DateTimeField(default=None, null=True)
    expiring = models.BooleanField(default=True)

    objects = ExpiringManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["expires"]),
            models.Index(fields=["expiring"]),
            models.Index(fields=["expiring", "expires"]),
        ]

    def expire_action(self, *args, **kwargs):
        """Handler which is called when this object is expired. By
        default the object is deleted. This is less efficient compared
        to bulk deleting objects, but classes like Token() need to change
        values instead of being deleted."""
        try:
            return self.delete(*args, **kwargs)
        except self.DoesNotExist:
            # Object has already been deleted, so this should be fine
            return None

    @classmethod
    def filter_not_expired(cls, **kwargs) -> models.QuerySet[Self]:
        """Filer for tokens which are not expired yet or are not expiring,
        and match filters in `kwargs`"""
        from authentik.events.models import Event

        deprecation_id = f"{class_to_path(cls)}.filter_not_expired"

        Event.log_deprecation(
            deprecation_id,
            message=(
                ".filter_not_expired() is deprecated as the default lookup now excludes "
                "expired objects."
            ),
        )

        for obj in (
            cls.objects.including_expired()
            .filter(**kwargs)
            .filter(Q(expires__lt=now(), expiring=True))
        ):
            obj.delete()
        return cls.objects.filter(**kwargs)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired yet."""
        if not self.expiring:
            return False
        return now() > self.expires
