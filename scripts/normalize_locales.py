#!/usr/bin/env python3
"""Move locale files onto their canonical paths.

Run via `make locales-normalize`. With `--check`, writes nothing and exits
non-zero if anything is out of place, which is what CI uses.

Transifex's `language_mapping` is global, so the PO filter receives hyphenated
directory names that Django cannot resolve. This renames them. It also recovers
any XLIFF that arrives under an upstream code rather than a canonical tag,
merging its translations into the canonical file rather than discarding them.

A path that resolves to nothing in the registry is an error: the repo decides
which languages exist, not Transifex.
"""

import shutil
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from authentik.lib.locales import Locale, load_registry, shipped_locales  # noqa: E402
from authentik.lib.xliff import drop_invalid_targets, merge_targets  # noqa: E402

ROOT = Path(__file__).parents[1]
XLIFF_DIR = ROOT / "web/xliff"
CATALOG_DIR = ROOT / "locale"


class UnknownLocale(Exception):
    """A path on disk corresponds to no registry row."""


def resolve(name: str) -> Locale | None:
    """Find the registry row a stray file or directory belongs to.

    Matches the canonical tag first, then the upstream Transifex code, then the
    catalog directory name. That covers every shape a stray can take: an
    upstream code (`pt_BR.xlf`), a hyphenated catalog directory (`locale/zh-Hans`),
    or a code the registry deliberately folds into another tag (`ar_AA`).
    """
    for locale in load_registry():
        if name in {locale.tag, locale.transifex, locale.django}:
            return locale
    return None


def merge_catalogs(stray: Path, destination: Path) -> None:
    """Fold one gettext catalog into another, the stray winning conflicts."""
    stray_po = stray / "LC_MESSAGES/django.po"
    destination_po = destination / "LC_MESSAGES/django.po"

    if not stray_po.is_file():
        return

    if not destination_po.is_file():
        destination_po.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(stray_po, destination_po)
        return

    # --use-first makes the earlier file win, so the stray goes first.
    merged = subprocess.run(  # noqa: S603
        ["msgcat", "--use-first", str(stray_po), str(destination_po)],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    )
    destination_po.write_text(merged.stdout, encoding="utf-8")


def normalize_xliff(*, check: bool) -> tuple[list[str], list[str]]:
    """Return (actions taken or needed, unresolvable paths)."""
    actions: list[str] = []
    unknown: list[str] = []

    for path in sorted(XLIFF_DIR.glob("*.xlf")):
        if path.stem == "en":
            continue

        locale = resolve(path.stem)
        if locale is None:
            unknown.append(str(path.relative_to(ROOT)))
            continue

        destination = XLIFF_DIR / f"{locale.tag}.xlf"
        if destination == path:
            continue

        if not destination.exists():
            actions.append(f"rename {path.name} -> {destination.name}")
            if not check:
                path.rename(destination)
            continue

        result = merge_targets(destination, path, write=not check)
        actions.append(
            f"merge {path.name} -> {destination.name} "
            f"({result.filled} filled, {result.replaced} replaced), then remove"
        )
        if not check:
            path.unlink()

    for locale in shipped_locales():
        path = XLIFF_DIR / f"{locale.tag}.xlf"
        if not path.is_file():
            continue
        dropped = drop_invalid_targets(path, write=not check)
        if dropped:
            actions.append(
                f"drop {dropped} unrenderable target(s) from {path.name} "
                "(placeholders disagree with the source)"
            )

    return actions, unknown


def normalize_catalogs(*, check: bool) -> tuple[list[str], list[str]]:
    actions: list[str] = []
    unknown: list[str] = []

    for path in sorted(CATALOG_DIR.iterdir()):
        if not path.is_dir():
            continue

        locale = resolve(path.name)
        if locale is None or locale.django is None:
            unknown.append(str(path.relative_to(ROOT)))
            continue

        destination = CATALOG_DIR / locale.django
        if destination == path:
            continue

        if not destination.exists():
            actions.append(f"rename locale/{path.name} -> locale/{destination.name}")
            if not check:
                path.rename(destination)
            continue

        actions.append(f"merge locale/{path.name} -> locale/{destination.name}, then remove")
        if not check:
            merge_catalogs(path, destination)
            shutil.rmtree(path)

    return actions, unknown


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit non-zero if anything is out of place",
    )
    arguments = parser.parse_args()

    xliff_actions, xliff_unknown = normalize_xliff(check=arguments.check)
    catalog_actions, catalog_unknown = normalize_catalogs(check=arguments.check)

    actions = xliff_actions + catalog_actions
    unknown = xliff_unknown + catalog_unknown

    for action in actions:
        print(("would " if arguments.check else "") + action)

    if unknown:
        print("\nThese paths match no row in locales.yaml:")
        for name in unknown:
            print(f"  {name}")
        print(
            "\nauthentik decides which languages exist. Add a row to locales.yaml "
            "(ship: false is fine) and run `make gen-locales`, or delete the file."
        )
        return 1

    if arguments.check and actions:
        print("\nRun `make locales-normalize` and commit the result.")
        return 1

    if not actions:
        print("Locale files are on their canonical paths.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
