# Standard Library
import os
from collections.abc import Iterator
from contextlib import contextmanager

# 3rd-party
from monkeytype.config import DefaultConfig


class MonkeyConfig(DefaultConfig):
    @contextmanager
    def cli_context(self, command: str) -> Iterator[None]:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
        import django

        django.setup()
        yield


CONFIG = MonkeyConfig()
