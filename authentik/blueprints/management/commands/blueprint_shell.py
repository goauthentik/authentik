"""Test and debug Blueprints"""

import atexit
import readline
from pathlib import Path
from pprint import pformat
from sys import exit as sysexit
from textwrap import indent

from django.core.management.base import BaseCommand, no_translations
from structlog.stdlib import get_logger
from yaml import load

from authentik.blueprints.v1.common import BlueprintLoader, EntryInvalidError
from authentik.common.utils.errors import exception_to_string
from authentik.core.management.commands.shell import get_banner_text

LOGGER = get_logger()


class Command(BaseCommand):
    """Test and debug Blueprints"""

    lines = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        histfolder = Path("~").expanduser() / Path(".local/share/authentik")
        histfolder.mkdir(parents=True, exist_ok=True)
        histfile = histfolder / Path("blueprint_shell_history")
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode vi")

        try:
            readline.read_history_file(str(histfile))
        except FileNotFoundError:
            pass

        atexit.register(readline.write_history_file, str(histfile))

    @no_translations
    def handle(self, *args, **options):
        """Interactively debug blueprint files"""
        self.stdout.write(get_banner_text("Blueprint shell"))
        self.stdout.write("Type '.eval' to evaluate previously entered statement(s).")

        def do_eval():
            yaml_input = "\n".join([line for line in self.lines if line])
            data = load(yaml_input, BlueprintLoader)
            self.stdout.write(pformat(data))
            self.lines = []

        while True:
            try:
                line = input("> ")
                if line == ".eval":
                    do_eval()
                else:
                    self.lines.append(line)
            except EntryInvalidError as exc:
                self.stdout.write("Failed to evaluate expression:")
                self.stdout.write(indent(exception_to_string(exc), prefix="  "))
            except EOFError:
                break
            except KeyboardInterrupt:
                self.stdout.write()
                sysexit(0)
        self.stdout.write()
