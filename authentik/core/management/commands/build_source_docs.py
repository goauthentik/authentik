"""Build source docs"""
from pathlib import Path

from django.core.management.base import BaseCommand
from pdoc import pdoc
from pdoc.render import configure


class Command(BaseCommand):
    """Build source docs"""

    def handle(self, **options):
        configure(
            docformat="markdown",
            mermaid=True,
            logo="https://goauthentik.io/img/icon_top_brand_colour.svg",
        )
        pdoc(
            "authentik",
            output_directory=Path("./source_docs"),
        )
