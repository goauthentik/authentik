"""Merge translation targets between XLIFF files.

Used to recover work stranded in a non-canonical file, and to reconcile a
locale whose source skeleton went stale while it was unshipped.

The merge rule, per the locale registry design:

    For each unit in the canonical file, if the donor has a non-empty target
    for that unit id, use it; otherwise keep what is already there.

The canonical file supplies the skeleton, so units the donor alone knows about
are dropped — they belong to an older extraction. Targets are spliced as text
rather than re-serialized, because they carry `<x/>` placeholder elements and
lit-localize's own formatting, both of which a round-trip through an XML writer
would disturb.
"""

import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

TRANS_UNIT = re.compile(r"(<trans-unit\b[^>]*>)(.*?)(</trans-unit>)", re.DOTALL)
UNIT_ID = re.compile(r'\bid="([^"]*)"')
TARGET = re.compile(r"<target\b[^>]*/>|<target\b[^>]*>.*?</target>", re.DOTALL)
SOURCE = re.compile(r"<source\b[^>]*/>|<source\b[^>]*>.*?</source>", re.DOTALL)
MARKUP = re.compile(r"<[^>]*>")
PLACEHOLDER = re.compile(r'<x\b[^>]*\bid="([^"]*)"')


@dataclass(frozen=True, slots=True)
class MergeResult:
    """What a merge did."""

    filled: int
    """Units that had no target and gained one."""

    replaced: int
    """Units whose existing target was overwritten by a differing donor target."""

    kept: int
    """Units left alone: the donor had nothing to offer."""

    rejected: int
    """Donor targets refused because their placeholders no longer match the source."""

    @property
    def changed(self) -> int:
        return self.filled + self.replaced


def normalized_text(target: str) -> str:
    """Translated text with markup and whitespace differences flattened away.

    Two targets that normalize alike say the same thing, even when their raw
    markup differs — usually because the donor came from an older extraction
    and carries stale `equiv-text` metadata, different line wrapping, or
    entity-escaped punctuation (`&quot;` where the other file has a literal
    quote). Entities are decoded so the comparison is semantic rather than
    byte-level; without that, escaping alone reads as a translation change.
    """
    return " ".join(unescape(MARKUP.sub("", target)).split())


def _is_populated(target: str | None) -> bool:
    """Whether a `<target>` element carries actual content."""
    if target is None:
        return False
    inner = MARKUP.sub("", target).strip()
    if inner:
        return True
    # A target holding only placeholders (<x/>) is still a real translation.
    return "<x " in target or "<x/>" in target


def read_targets(path: Path) -> dict[str, str]:
    """Map unit id to its raw `<target>` element, skipping empty ones."""
    body = path.read_text(encoding="utf-8")
    targets: dict[str, str] = {}

    for opening, inner, _ in TRANS_UNIT.findall(body):
        identifier = UNIT_ID.search(opening)
        if identifier is None:
            continue
        found = TARGET.search(inner)
        if found is None:
            continue
        if _is_populated(found.group(0)):
            targets[identifier.group(1)] = found.group(0)

    return targets


def drop_invalid_targets(path: Path, *, write: bool = True) -> int:
    """Remove targets whose placeholders disagree with their source.

    A target that declares different placeholders than its source cannot render
    — the substitution has nowhere to go — and lit-localize refuses to build it.
    These arrive when a language sat unshipped while the source moved on, so
    nothing ever validated its translations. Dropping the target falls back to
    English for that one string and lets the rest of the language ship.
    """
    body = path.read_text(encoding="utf-8")
    dropped = 0

    def rewrite(match: re.Match[str]) -> str:
        nonlocal dropped

        opening, inner, closing = match.groups()
        source = SOURCE.search(inner)
        target = TARGET.search(inner)
        if source is None or target is None or not _is_populated(target.group(0)):
            return match.group(0)

        if set(PLACEHOLDER.findall(target.group(0))) == set(PLACEHOLDER.findall(source.group(0))):
            return match.group(0)

        dropped += 1
        # Take the whole line the target sits on, so no blank line is left.
        line_start = inner.rfind("\n", 0, target.start()) + 1
        return opening + inner[:line_start] + inner[target.end() :].lstrip("\n") + closing

    cleaned = TRANS_UNIT.sub(rewrite, body)

    if write and cleaned != body:
        path.write_text(cleaned, encoding="utf-8")

    return dropped


def merge_targets(canonical: Path, donor: Path, *, write: bool = True) -> MergeResult:
    """Apply the merge rule, donor winning conflicts. Returns what changed."""
    donated = read_targets(donor)
    body = canonical.read_text(encoding="utf-8")

    filled = replaced = kept = rejected = 0

    def rewrite(match: re.Match[str]) -> str:
        nonlocal filled, replaced, kept, rejected

        opening, inner, closing = match.groups()
        identifier = UNIT_ID.search(opening)
        if identifier is None:
            return match.group(0)

        incoming = donated.get(identifier.group(1))
        if incoming is None:
            kept += 1
            return match.group(0)

        # The source states which placeholders a translation must carry. A donor
        # from an older extraction can disagree — it may predate a placeholder
        # being added, or carry one since removed. Taking it would drop a runtime
        # substitution and fail the locale build, so refuse it outright.
        source_element = SOURCE.search(inner)
        if source_element is not None:
            required = set(PLACEHOLDER.findall(source_element.group(0)))
            if set(PLACEHOLDER.findall(incoming)) != required:
                rejected += 1
                return match.group(0)

        existing = TARGET.search(inner)

        if existing is not None and _is_populated(existing.group(0)):
            # Keep what is here unless the donor actually says something
            # different. The canonical file holds the newer skeleton, so its
            # placeholder metadata and formatting are the ones worth keeping.
            if normalized_text(existing.group(0)) == normalized_text(incoming):
                kept += 1
                return match.group(0)
            replaced += 1
            inner = inner[: existing.start()] + incoming + inner[existing.end() :]
            return opening + inner + closing

        filled += 1

        if existing is not None:
            # Replace an empty <target/> in place.
            inner = inner[: existing.start()] + incoming + inner[existing.end() :]
            return opening + inner + closing

        # No target at all: insert directly after <source>, matching its indent.
        source = SOURCE.search(inner)
        if source is None:
            kept += 1
            return match.group(0)

        line_start = inner.rfind("\n", 0, source.start()) + 1
        indent = inner[line_start : source.start()]
        inner = inner[: source.end()] + "\n" + indent + incoming + inner[source.end() :]
        return opening + inner + closing

    merged = TRANS_UNIT.sub(rewrite, body)

    if write and merged != body:
        canonical.write_text(merged, encoding="utf-8")

    return MergeResult(filled=filled, replaced=replaced, kept=kept, rejected=rejected)
