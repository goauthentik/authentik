"""Keep translation files, generated locale lists, and Transifex in line with locales.yaml.

Usage:
    python scripts/locales.py gen        Rewrite the files generated from the registry.
    python scripts/locales.py normalize  Move translation files to their canonical paths.
    python scripts/locales.py check      Exit non-zero if anything drifted from the registry.

Transifex substitutes its own language code into both of the paths in
.github/transifex.yml, and its language mapping is global. The mapping sends every
code to the web tag (pt_BR -> pt-BR), which is what web/xliff/ needs. `normalize`
then moves backend catalogs from locale/<tag>/ to the directory Django reads,
locale/<to_locale(tag)>/. See https://github.com/goauthentik/authentik/issues/24563.
"""

import html
import json
import re
import shutil
import subprocess  # nosec
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml
from django.utils.translation import to_locale

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "locales.yaml"
LOCALE_DIR = ROOT / "locale"
XLIFF_DIR = ROOT / "web" / "xliff"
LIT_LOCALIZE = ROOT / "web" / "lit-localize.json"
DEFINITIONS = ROOT / "web" / "src" / "common" / "ui" / "locale" / "definitions.ts"
TRANSIFEX = ROOT / ".github" / "transifex.yml"

SOURCE_TAG = "en"
PSEUDO_TAG = "en-XA"
GENERATED_NOTE = "Generated from locales.yaml by `make gen-locales`. Do not edit by hand."
REGION_START = "// #region Generated locale loaders"
REGION_END = "// #endregion"


@dataclass(frozen=True)
class Locale:
    tag: str
    django: str | None
    transifex: str | None
    ship: bool


def load_registry() -> list[Locale]:
    rows = yaml.safe_load(REGISTRY.read_text())["locales"]
    return [Locale(**row) for row in rows]


# region Generated files


def render_lit_localize(registry: list[Locale]) -> str:
    config = json.loads(LIT_LOCALIZE.read_text())
    config["targetLocales"] = [row.tag for row in registry if row.ship]
    return json.dumps(config, indent=4, ensure_ascii=False) + "\n"


def render_definitions(registry: list[Locale]) -> str:
    text = DEFINITIONS.read_text()
    start = text.index(REGION_START)
    end = text.index(REGION_END, start)
    indent = text[text.rindex("\n", 0, start) + 1 : start]
    loaders = [
        f'{indent}"{row.tag}": () => import("#locales/{row.tag}"),'
        for row in registry
        if row.ship and row.tag not in (SOURCE_TAG, PSEUDO_TAG)
    ]
    body = "\n".join([REGION_START, *loaders, indent])
    return text[:start] + body + text[end:]


def render_transifex(registry: list[Locale]) -> str:
    text = TRANSIFEX.read_text()
    if "\nsettings:" in text:
        text = text[: text.index("\nsettings:")]
    text = text.rstrip("\n") + "\n"
    mapping = [
        f"    {row.transifex}: {row.tag}"
        for row in registry
        if row.transifex and row.transifex != row.tag
    ]
    settings = ["", "settings:", f"  # {GENERATED_NOTE}", "  language_mapping:", *mapping]
    return text + "\n".join(settings) + "\n"


def generated(registry: list[Locale]) -> dict[Path, str]:
    return {
        LIT_LOCALIZE: render_lit_localize(registry),
        DEFINITIONS: render_definitions(registry),
        TRANSIFEX: render_transifex(registry),
    }


# endregion

# region Normalization


def canonical_dir_for(name: str, registry: list[Locale]) -> str | None:
    """The canonical locale/ directory for a directory Transifex may have created."""
    for row in registry:
        if row.django and name in (row.tag, row.transifex, row.django):
            return row.django
    return None


def canonical_tag_for(stem: str, registry: list[Locale]) -> str | None:
    """The canonical web/xliff/ tag for an xliff file Transifex may have created."""
    for row in registry:
        if stem in (row.tag, row.transifex, row.django):
            return row.tag
    return None


def merge_po(incoming: Path, canonical: Path) -> None:
    """Fold `incoming` into `canonical`. Incoming translations win; its msgids are kept."""
    with tempfile.TemporaryDirectory() as tmp:
        translated = Path(tmp) / "translated.po"
        union = Path(tmp) / "union.po"
        # Untranslated entries would otherwise shadow the canonical translations.
        subprocess.run(  # nosec
            ["msgattrib", "--translated", "--no-obsolete", "-o", translated, incoming], check=True
        )
        subprocess.run(  # nosec
            ["msgcat", "--use-first", "-o", union, translated, canonical], check=True
        )
        subprocess.run(  # nosec
            ["msgmerge", "--quiet", "--no-fuzzy-matching", "-o", canonical, union, incoming],
            check=True,
        )


def normalize_locale_dirs(registry: list[Locale]) -> list[str]:
    actions = []
    for path in sorted(p for p in LOCALE_DIR.iterdir() if p.is_dir()):
        target_name = canonical_dir_for(path.name, registry)
        if target_name is None or target_name == path.name:
            continue
        target = LOCALE_DIR / target_name
        if not target.exists():
            path.rename(target)
            actions.append(f"locale/{path.name} -> locale/{target_name}")
            continue
        incoming_po = path / "LC_MESSAGES" / "django.po"
        target_po = target / "LC_MESSAGES" / "django.po"
        if incoming_po.exists():
            if target_po.exists():
                merge_po(incoming_po, target_po)
            else:
                target_po.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(incoming_po, target_po)
            subprocess.run(  # nosec
                ["msgfmt", "-o", target_po.with_suffix(".mo"), target_po], check=True
            )
        shutil.rmtree(path)
        actions.append(f"locale/{path.name} merged into locale/{target_name}")
    return actions


UNIT = re.compile(r'(<trans-unit id="([^"]+)"[^>]*>)(.*?)(</trans-unit>)', re.S)
SOURCE = re.compile(r"<source>(.*?)</source>", re.S)
TARGET = re.compile(r"<target>(.*?)</target>", re.S)
PLACEHOLDER = re.compile(r'<x\b[^>]*?\bid="([^"]+)"[^>]*/>')


def comparable(text: str) -> str:
    text = PLACEHOLDER.sub(lambda m: "{x" + m.group(1) + "}", text)
    # Transifex double-escapes some entities; decode until stable.
    while (decoded := html.unescape(text)) != text:
        text = decoded
    return re.sub(r"\s+", " ", text).strip()


def merge_xliff(donor: Path, canonical: Path) -> None:
    """Fold `donor` targets into `canonical`. Donor targets win when their source matches.

    Only a donor target whose <source> and placeholder ids match the canonical unit is
    taken, so a translation of an older source string never attaches to a changed
    message. Placeholders are copied from the canonical source to keep equiv-text current.
    """
    donor_units = {}
    for _, uid, body, _ in UNIT.findall(donor.read_text()):
        src, tgt = SOURCE.search(body), TARGET.search(body)
        if src and tgt and tgt.group(1).strip():
            donor_units[uid] = (src.group(1), tgt.group(1))

    def rewrite(match: re.Match) -> str:
        head, uid, body, tail = match.groups()
        src = SOURCE.search(body)
        if not src or uid not in donor_units:
            return match.group(0)
        donor_source, donor_target = donor_units[uid]
        source = src.group(1)
        if comparable(donor_source) != comparable(source):
            return match.group(0)
        if Counter(PLACEHOLDER.findall(donor_target)) != Counter(PLACEHOLDER.findall(source)):
            return match.group(0)
        placeholders = {m.group(1): m.group(0) for m in PLACEHOLDER.finditer(source)}
        target = PLACEHOLDER.sub(lambda m: placeholders[m.group(1)], donor_target)
        current = TARGET.search(body)
        if current:
            body = body[: current.start(1)] + target + body[current.end(1) :]
        else:
            indent = re.search(r"\n([ \t]*)<source>", body)
            pad = indent.group(1) if indent else "  "
            body = body[: src.end()] + f"\n{pad}<target>{target}</target>" + body[src.end() :]
        return head + body + tail

    canonical.write_text(UNIT.sub(rewrite, canonical.read_text()))


def normalize_xliff_files(registry: list[Locale]) -> list[str]:
    actions = []
    for path in sorted(XLIFF_DIR.glob("*.xlf")):
        tag = canonical_tag_for(path.stem, registry)
        if tag is None or tag == path.stem:
            continue
        target = XLIFF_DIR / f"{tag}.xlf"
        if target.exists():
            merge_xliff(path, target)
            path.unlink()
            actions.append(f"web/xliff/{path.name} merged into web/xliff/{target.name}")
        else:
            language = f'target-language="{tag}"'
            text = re.sub(r'target-language="[^"]*"', language, path.read_text(), count=1)
            target.write_text(text)
            path.unlink()
            actions.append(f"web/xliff/{path.name} -> web/xliff/{target.name}")
    return actions


# endregion

# region Checks


def check(registry: list[Locale]) -> list[str]:
    errors = []
    tags = Counter(row.tag for row in registry)
    errors += [f"locales.yaml: duplicate tag {tag}" for tag, n in tags.items() if n > 1]

    for row in registry:
        if row.django and row.django != to_locale(row.tag):
            errors.append(
                f"locales.yaml: {row.tag} has django: {row.django}, expected {to_locale(row.tag)}"
            )
        if not row.ship or row.tag in (SOURCE_TAG, PSEUDO_TAG):
            continue
        if not (XLIFF_DIR / f"{row.tag}.xlf").exists():
            errors.append(f"web/xliff/{row.tag}.xlf is missing for shipped locale {row.tag}")
        if row.django and not (LOCALE_DIR / row.django / "LC_MESSAGES" / "django.po").exists():
            errors.append(f"locale/{row.django}/ is missing for shipped locale {row.tag}")

    django_dirs = {row.django for row in registry if row.django}
    for path in sorted(p for p in LOCALE_DIR.iterdir() if p.is_dir()):
        if path.name not in django_dirs:
            errors.append(f"locale/{path.name}/ isn't a canonical directory in locales.yaml")

    xliff_tags = {row.tag for row in registry}
    for path in sorted(XLIFF_DIR.glob("*.xlf")):
        if path.stem not in xliff_tags:
            errors.append(f"web/xliff/{path.name} isn't a canonical file in locales.yaml")

    for path, expected in generated(registry).items():
        if path.read_text() != expected:
            errors.append(f"{path.relative_to(ROOT)} is out of date")

    return errors


# endregion


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    registry = load_registry()

    if command == "gen":
        for path, content in generated(registry).items():
            path.write_text(content)
        return 0

    if command == "normalize":
        for action in normalize_locale_dirs(registry) + normalize_xliff_files(registry):
            print(action)
        return 0

    if command == "check":
        errors = check(registry)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        if errors:
            print(
                "\nRun `make locales-normalize gen-locales`,"
                " or register the locale in locales.yaml.",
                file=sys.stderr,
            )
        return 1 if errors else 0

    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
