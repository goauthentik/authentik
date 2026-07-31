"""Access to the canonical locale registry.

`locales.yaml` at the repository root is the source of truth for every language
authentik knows about. This module loads it and enforces the invariants every
consumer relies on, so a malformed registry fails at import rather than halfway
through a generator run.
"""

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from django.utils.translation import to_locale
from yaml import safe_load

REGISTRY_PATH = Path(__file__).parents[2] / "locales.yaml"

XLIFF_DIR = Path("web/xliff")
CATALOG_DIR = Path("locale")


class RegistryError(ValueError):
    """Raised when the registry violates an invariant."""


@dataclass(frozen=True, slots=True)
class Locale:
    """One row of the registry."""

    tag: str
    """BCP-47 identity. Names the XLIFF file and the lit-localize target locale."""

    django: str | None
    """Directory under `locale/`, or None for locales with no backend catalog."""

    transifex: str | None
    """Upstream Transifex code, or None when not translated upstream."""

    ship: bool
    """Whether the tag is emitted into `web/lit-localize.json` targetLocales."""

    @property
    def xliff_path(self) -> Path:
        return XLIFF_DIR / f"{self.tag}.xlf"

    @property
    def catalog_path(self) -> Path | None:
        """Path to the gettext catalog directory, if this locale has one."""
        if self.django is None:
            return None
        return CATALOG_DIR / self.django


def _validate(locales: tuple[Locale, ...]) -> None:
    if not locales:
        raise RegistryError(f"{REGISTRY_PATH} contains no locales")

    seen_tags: set[str] = set()
    seen_transifex: set[str] = set()

    for locale in locales:
        if locale.tag in seen_tags:
            raise RegistryError(f"duplicate tag {locale.tag!r}")
        seen_tags.add(locale.tag)

        if locale.transifex is not None:
            if locale.transifex in seen_transifex:
                raise RegistryError(
                    f"upstream code {locale.transifex!r} is mapped by more than one tag; "
                    "language_mapping cannot express that"
                )
            seen_transifex.add(locale.transifex)

        # The invariant that makes locale/zh-Hans impossible to reintroduce: a
        # catalog directory Django cannot resolve is a directory Django ignores.
        if locale.django is not None and locale.django != to_locale(locale.tag):
            raise RegistryError(
                f"{locale.tag!r} declares catalog {locale.django!r}, but Django resolves "
                f"that tag to {to_locale(locale.tag)!r}"
            )


@cache
def load_registry(path: Path = REGISTRY_PATH) -> tuple[Locale, ...]:
    """Load and validate the registry, sorted by tag."""
    document = safe_load(path.read_text(encoding="utf-8"))
    try:
        rows = document["locales"]
    except (TypeError, KeyError) as exc:
        raise RegistryError(f"{path} has no top-level 'locales' key") from exc

    locales = tuple(
        sorted(
            (
                Locale(
                    tag=row["tag"],
                    django=row["django"],
                    transifex=row["transifex"],
                    ship=row["ship"],
                )
                for row in rows
            ),
            key=lambda locale: locale.tag,
        )
    )
    _validate(locales)
    return locales


def shipped_locales() -> tuple[Locale, ...]:
    """Locales built into the web UI."""
    return tuple(locale for locale in load_registry() if locale.ship)


def target_locales() -> tuple[str, ...]:
    """Tags for `web/lit-localize.json` targetLocales."""
    return tuple(locale.tag for locale in shipped_locales())


def language_mapping() -> dict[str, str]:
    """Upstream code to canonical tag, for `.github/transifex.yml`.

    Covers unshipped locales too: an unshipped language should still land on a
    canonical path rather than tripping the CI gate.
    """
    return {
        locale.transifex: locale.tag for locale in load_registry() if locale.transifex is not None
    }


def catalog_locales() -> tuple[Locale, ...]:
    """Locales that have a backend gettext catalog."""
    return tuple(locale for locale in load_registry() if locale.django is not None)


def known_xliff_names() -> frozenset[str]:
    """Every XLIFF filename the registry permits in `web/xliff/`."""
    return frozenset(f"{locale.tag}.xlf" for locale in load_registry())


def known_catalog_names() -> frozenset[str]:
    """Every directory name the registry permits in `locale/`."""
    return frozenset(locale.django for locale in load_registry() if locale.django is not None)
