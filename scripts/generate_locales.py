#!/usr/bin/env python3
"""Regenerate every file derived from the canonical locale registry.

Run via `make gen-locales`. With `--check`, writes nothing and exits non-zero if
any target has drifted, which is what CI uses.

Targets:
    web/lit-localize.json                       targetLocales
    web/src/common/ui/locale/definitions.ts     LocaleLoaderRecord entries
    .github/transifex.yml                       settings.language_mapping
"""

import sys
from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from authentik.lib.locales import (  # noqa: E402
    language_mapping,
    shipped_locales,
    target_locales,
)

ROOT = Path(__file__).parents[1]

LIT_LOCALIZE = ROOT / "web/lit-localize.json"
DEFINITIONS = ROOT / "web/src/common/ui/locale/definitions.ts"
TRANSIFEX = ROOT / ".github/transifex.yml"

# Tags handled by hand in definitions.ts: the source locale resolves to a stub
# module and the pseudo-locale is keyed off a named constant.
UNGENERATED_TAGS = frozenset({"en", "en-XA"})


class DriftError(Exception):
    """A generated file does not match the registry."""


def replace_region(body: str, marker: str, replacement: str, path: Path) -> str:
    """Swap the text between `<generated:marker>` and `</generated:marker>`."""
    opening = f"<generated:{marker}>"
    closing = f"</generated:{marker}>"

    try:
        start = body.index(opening)
        end = body.index(closing)
    except ValueError as exc:
        raise DriftError(f"{path} is missing the {opening} region") from exc

    # Keep the marker lines themselves, including their indentation and comment
    # syntax, and replace only what sits between them.
    start = body.index("\n", start) + 1
    end = body.rindex("\n", 0, end) + 1
    return body[:start] + replacement + body[end:]


def render_lit_localize(body: str) -> str:
    config = loads(body)
    config["targetLocales"] = list(target_locales())
    return dumps(config, indent=4, ensure_ascii=False) + "\n"


def render_definitions(body: str) -> str:
    lines = [
        f'    "{locale.tag}": () => import("#locales/{locale.tag}"),'
        for locale in shipped_locales()
        if locale.tag not in UNGENERATED_TAGS
    ]
    return replace_region(body, "locale-loaders", "\n".join(lines) + "\n", DEFINITIONS)


def render_transifex(body: str) -> str:
    mapping = language_mapping()
    lines = [f"    {upstream}: {tag}" for upstream, tag in sorted(mapping.items())]
    return replace_region(body, "language-mapping", "\n".join(lines) + "\n", TRANSIFEX)


TARGETS = (
    (LIT_LOCALIZE, render_lit_localize),
    (DEFINITIONS, render_definitions),
    (TRANSIFEX, render_transifex),
)


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit non-zero if a target has drifted",
    )
    arguments = parser.parse_args()

    drifted: list[Path] = []

    for path, render in TARGETS:
        current = path.read_text(encoding="utf-8")
        updated = render(current)

        if current == updated:
            continue

        drifted.append(path)
        if not arguments.check:
            path.write_text(updated, encoding="utf-8")

    relative = [str(path.relative_to(ROOT)) for path in drifted]

    if arguments.check:
        if drifted:
            print("Locale files are out of sync with locales.yaml:")
            for name in relative:
                print(f"  {name}")
            print("\nRun `make gen-locales` and commit the result.")
            return 1
        print("Locale files are in sync with locales.yaml.")
        return 0

    if drifted:
        for name in relative:
            print(f"regenerated {name}")
    else:
        print("Locale files were already in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
