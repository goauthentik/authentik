import os
import warnings
from functools import update_wrapper
from types import FunctionType

from cryptography.hazmat.backends.openssl.backend import backend
from defusedxml import defuse_stdlib
from xmlsec import base64_default_line_size

from authentik.lib.config import CONFIG


def _keep_field_classes_cacheable():
    """Django's and DRF's `Field.__init__` count instances in a class attribute, so every field
    created modifies the `Field` class. CPython stops caching attribute lookups for a class that
    was modified more than 1000 times, and for all its subclasses: every model field, serializer
    and serializer field. Lookups on those then take a lock that is global to the interpreter,
    which is slow with the GIL and makes threads queue up without it.

    Hand both `__init__`s a stand-in for `Field` that keeps the counters instead. This has to
    run before models and serializers are imported, as the class can't recover afterwards."""
    from django.db.models import fields as django_fields
    from rest_framework import fields as drf_fields

    for module in (django_fields, drf_fields):
        cls = module.Field
        init = cls.__init__
        if getattr(init, "_keeps_class_cacheable", False):
            continue

        class Counters:
            # DRF's `__init__` also compares `self.__class__ == Field`
            def __eq__(self, other, cls=cls):
                return other is cls or other is self

            __hash__ = object.__hash__

        counters = Counters()
        for name, value in vars(cls).items():
            if name.endswith("creation_counter"):
                setattr(counters, name, value)
        new_init = FunctionType(
            init.__code__,
            {**module.__dict__, "Field": counters},
            init.__name__,
            init.__defaults__,
            init.__closure__,
        )
        new_init.__kwdefaults__ = init.__kwdefaults__
        update_wrapper(new_init, init)
        new_init._keeps_class_cacheable = True
        cls.__init__ = new_init


def setup():
    _keep_field_classes_cacheable()
    warnings.filterwarnings("ignore", "SelectableGroups dict interface")
    warnings.filterwarnings(
        "ignore",
        "defusedxml.lxml is no longer supported and will be removed in a future release.",
    )
    warnings.filterwarnings(
        "ignore",
        "defusedxml.cElementTree is deprecated, import from defusedxml.ElementTree instead.",
    )

    defuse_stdlib()
    base64_default_line_size(size=8192)

    if CONFIG.get_bool("compliance.fips.enabled", False):
        backend._enable_fips()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
