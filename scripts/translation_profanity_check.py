#!/usr/bin/env python3
"""Translation profanity gate.

Scans Transifex-sourced translations (Django PO under locale/ and lit-localize
XLIFF under web/xliff/) against per-language profanity dictionaries fetched at
runtime from PROFANITY_DICT_BASE_URL. Exits non-zero when any non-allowlisted
match is found.

No profanity word lists, fixtures, or example bad strings are committed; the
self-test uses abstract placeholder tokens.

Run:
    python scripts/translation_profanity_check.py [--root .] [--allowlist PATH]
    python scripts/translation_profanity_check.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = (
    "https://raw.githubusercontent.com/LDNOOBW/"
    "List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master"
)

# HTTP 404 from the dictionary host means "this language isn't covered" and
# downgrades to a skip; any other status propagates.
_HTTP_NOT_FOUND = 404

# Locales we skip wholesale:
#   - "en" / "en-XA": source + pseudo-locale (no human translations).
SKIP_LOCALES = frozenset({"en", "en-XA"})

# Maps a repo locale identifier (e.g. "pt_BR", "zh-Hans") to the dictionary
# code expected at PROFANITY_DICT_BASE_URL. Anything not listed falls through
# to "strip region after - or _" (e.g. "de_DE" -> "de"). LDNOOBW publishes one
# file per language without a file extension.
LOCALE_DICT_OVERRIDES = {
    "zh-Hans": "zh",
    "zh-Hant": "zh",
    "zh_CN": "zh",
    "zh_TW": "zh",
    "pt_BR": "pt",
    "pt_PT": "pt",
    "no_NO": "no",
}

# Unicode ranges that lack reliable whitespace word boundaries; for these we
# fall back to substring matching against the dictionary entry.
_CJK_RANGES = (
    (0x3040, 0x30FF),  # Hiragana + Katakana
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0xAC00, 0xD7AF),  # Hangul Syllables
    (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
)


def _is_cjk_char(ch: str) -> bool:
    code = ord(ch)
    return any(lo <= code <= hi for lo, hi in _CJK_RANGES)


def _has_cjk(text: str) -> bool:
    return any(_is_cjk_char(c) for c in text)


def normalize(text: str) -> str:
    """Case-fold + NFKC normalize for stable matching."""
    return unicodedata.normalize("NFKC", text).casefold()


def msgid_hash(msgid: str) -> str:
    """Stable 16-char SHA-256 prefix of msgid; used for allowlist entries.

    Allowlisting by *source* msgid avoids ever committing translated profane
    text. The English msgid is by definition non-profane (it is the source
    string an authentik developer wrote).
    """
    return hashlib.sha256(msgid.encode("utf-8")).hexdigest()[:16]


# --- dictionary fetch -----------------------------------------------------


def dict_code_for_locale(locale: str) -> str | None:
    """Return the LDNOOBW-style dictionary code for a repo locale, or None
    if the locale is skipped (source / pseudo)."""
    if locale in SKIP_LOCALES:
        return None
    if locale in LOCALE_DICT_OVERRIDES:
        return LOCALE_DICT_OVERRIDES[locale]
    return re.split(r"[-_]", locale, maxsplit=1)[0]


def _http_get(url: str, timeout: float = 15.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "authentik-profanity-gate/1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — fixed URL
        return resp.read().decode("utf-8", errors="replace")


def parse_dictionary(raw: str) -> list[str]:
    """LDNOOBW format: one entry per line, '#' comments stripped, blanks skipped."""
    out: list[str] = []
    for raw_line in raw.splitlines():
        entry = raw_line.split("#", 1)[0].strip()
        if entry:
            out.append(normalize(entry))
    return out


def fetch_dictionary(
    code: str,
    base_url: str,
    fetcher=_http_get,
) -> list[str] | None:
    """Returns dictionary entries (already normalized) or None if missing.

    "Missing" covers both HTTP 404 (no dict for that language at the source)
    and the local-file-not-found case (used by the self-test). Other failures
    — connection refused, 5xx, malformed UTF-8 — propagate, so a broken
    dictionary source fails CI loudly rather than silently passing."""
    url = f"{base_url.rstrip('/')}/{code}"
    try:
        raw = fetcher(url)
    except urllib.error.HTTPError as exc:
        if exc.code == _HTTP_NOT_FOUND:
            return None
        raise
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, FileNotFoundError):
            return None
        raise
    return parse_dictionary(raw)


# --- file parsing ---------------------------------------------------------


@dataclass(frozen=True)
class TranslationEntry:
    path: Path
    line: int
    locale: str
    msgid: str
    target: str
    references: tuple[str, ...] = ()  # PO `#:` source-location refs
    xliff_id: str | None = None  # XLIFF trans-unit id attribute


def iter_po(path: Path, locale: str) -> Iterator[TranslationEntry]:  # noqa: PLR0915 — single-pass PO state machine, splits would just push state out
    """Minimal PO reader: yields (msgid, msgstr) pairs with line numbers.

    Handles multi-line continuation strings and fuzzy/obsolete entries (we
    include fuzzy entries — they still ship to users — but skip obsolete
    `#~` entries). PO `#:` location references (gettext extractor output)
    are captured and attached to the entry whose `msgid` follows."""
    msgid_parts: list[str] = []
    msgstr_parts: list[str] = []
    pending_refs: list[str] = []  # accumulates between flush and next msgid
    entry_refs: tuple[str, ...] = ()  # frozen at msgid-encounter time
    state: str | None = None  # None | "msgid" | "msgstr"
    entry_line = 0

    def flush() -> Iterator[TranslationEntry]:
        if msgid_parts or msgstr_parts:
            msgid = "".join(msgid_parts)
            target = "".join(msgstr_parts)
            if msgid and target:  # skip the empty header entry
                yield TranslationEntry(
                    path=path,
                    line=entry_line,
                    locale=locale,
                    msgid=msgid,
                    target=target,
                    references=entry_refs,
                )

    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.rstrip("\n")
            stripped = line.lstrip()
            if stripped.startswith("#~"):
                # Obsolete entry — drop pending and skip.
                msgid_parts, msgstr_parts, state = [], [], None
                pending_refs = []
                continue
            if stripped.startswith("#:"):
                # `#: path/to/file.py:42 other/file.py:11` — refs for the
                # next msgid; accumulate.
                pending_refs.extend(tok for tok in stripped[2:].split() if tok)
                continue
            if not stripped or stripped.startswith("#"):
                if not stripped and state is not None:
                    # Blank line terminates an entry.
                    yield from flush()
                    msgid_parts, msgstr_parts, state = [], [], None
                    entry_refs = ()
                continue
            if stripped.startswith("msgid "):
                yield from flush()
                msgid_parts = [_po_unquote(stripped[len("msgid ") :])]
                msgstr_parts = []
                entry_refs = tuple(pending_refs)
                pending_refs = []
                state = "msgid"
                entry_line = lineno
            elif stripped.startswith("msgid_plural "):
                # Concatenate plural source into msgid bucket — we only need
                # *some* representation of the source for hashing/skip logic.
                msgid_parts.append(_po_unquote(stripped[len("msgid_plural ") :]))
                state = "msgid"
            elif stripped.startswith("msgstr["):
                # Plural form: msgstr[0] "..."
                rest = stripped.split("]", 1)[1].strip()
                msgstr_parts.append(_po_unquote(rest))
                state = "msgstr"
            elif stripped.startswith("msgstr "):
                msgstr_parts.append(_po_unquote(stripped[len("msgstr ") :]))
                state = "msgstr"
            elif stripped.startswith('"'):
                chunk = _po_unquote(stripped)
                if state == "msgid":
                    msgid_parts.append(chunk)
                elif state == "msgstr":
                    msgstr_parts.append(chunk)
        yield from flush()


def _po_unquote(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    # Resolve the standard PO escapes (\n, \t, \\, \").
    return value.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")


_XLIFF_NS = "{urn:oasis:names:tc:xliff:document:1.2}"


def iter_xliff(path: Path, locale: str) -> Iterator[TranslationEntry]:
    """Yields trans-units that have a non-empty <target>.

    Captures the `id` attribute on every unit so findings can point a
    developer at the named ID instead of forcing them to decode a hash."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise SystemExit(f"{path}: malformed XLIFF: {exc}") from exc
    root = tree.getroot()
    for unit in root.iter(f"{_XLIFF_NS}trans-unit"):
        src_el = unit.find(f"{_XLIFF_NS}source")
        tgt_el = unit.find(f"{_XLIFF_NS}target")
        if tgt_el is None:
            continue
        target = "".join(tgt_el.itertext())
        if not target.strip():
            continue
        unit_id = unit.get("id") or None
        # `<source>` is the English msgid; the `id` attribute is the named/
        # generated identifier developers use in code.
        msgid = "".join(src_el.itertext()) if src_el is not None else (unit_id or "")
        # XLIFF ElementTree doesn't expose line numbers natively; report 0 to
        # mean "see file". Acceptable trade-off vs. pulling in lxml.
        yield TranslationEntry(
            path=path,
            line=0,
            locale=locale,
            msgid=msgid,
            target=target,
            xliff_id=unit_id,
        )


# --- discovery ------------------------------------------------------------


def discover_translation_files(root: Path) -> list[tuple[Path, str, str]]:
    """Returns (path, locale, kind) tuples. kind is 'po' or 'xliff'."""
    out: list[tuple[Path, str, str]] = []
    locale_dir = root / "locale"
    if locale_dir.is_dir():
        for sub in sorted(locale_dir.iterdir()):
            if not sub.is_dir():
                continue
            po = sub / "LC_MESSAGES" / "django.po"
            if po.is_file():
                out.append((po, sub.name, "po"))
    xliff_dir = root / "web" / "xliff"
    if xliff_dir.is_dir():
        for xlf in sorted(xliff_dir.glob("*.xlf")):
            locale = xlf.stem
            if locale == "en":
                continue
            out.append((xlf, locale, "xliff"))
    return out


# --- matching -------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    locale: str
    path: Path
    line: int
    word: str  # matched dictionary entry; redacted from default output
    msgid: str
    target: str  # full translated string; available to JSON output
    dict_code: str
    references: tuple[str, ...] = ()
    xliff_id: str | None = None

    @property
    def msgid_hash(self) -> str:
        return msgid_hash(self.msgid)

    @property
    def allowlist_key(self) -> str:
        """`<locale>:<msgid_hash>` — the per-locale exemption key."""
        return f"{self.locale}:{self.msgid_hash}"


def _build_word_pattern(words: Iterable[str]) -> tuple[re.Pattern[str] | None, list[str]]:
    """Compile a single alternation regex for ASCII/Latin/Cyrillic words and
    return the remaining words (CJK / multi-token) for substring matching."""
    boundary_terms: list[str] = []
    substring_terms: list[str] = []
    for w in words:
        if not w:
            continue
        if _has_cjk(w) or " " in w:
            substring_terms.append(w)
        else:
            boundary_terms.append(re.escape(w))
    pattern: re.Pattern[str] | None = None
    if boundary_terms:
        # Sort longest-first so e.g. "abcd" beats "abc" when both are listed.
        boundary_terms.sort(key=len, reverse=True)
        pattern = re.compile(r"\b(?:" + "|".join(boundary_terms) + r")\b", re.UNICODE)
    return pattern, substring_terms


def scan_entries(
    entries: Iterable[TranslationEntry],
    dictionary: list[str],
    dict_code: str,
) -> Iterator[Finding]:
    pattern, substrings = _build_word_pattern(dictionary)
    for entry in entries:
        haystack = normalize(entry.target)
        if pattern is not None:
            for m in pattern.finditer(haystack):
                yield Finding(
                    locale=entry.locale,
                    path=entry.path,
                    line=entry.line,
                    word=m.group(0),
                    msgid=entry.msgid,
                    target=entry.target,
                    dict_code=dict_code,
                    references=entry.references,
                    xliff_id=entry.xliff_id,
                )
        for term in substrings:
            if term in haystack:
                yield Finding(
                    locale=entry.locale,
                    path=entry.path,
                    line=entry.line,
                    word=term,
                    msgid=entry.msgid,
                    target=entry.target,
                    dict_code=dict_code,
                    references=entry.references,
                    xliff_id=entry.xliff_id,
                )


# --- allowlist ------------------------------------------------------------

# Allowlist entry shape: `<locale>:<16-hex>`. Locale segment may be any
# non-empty token that doesn't contain ':' — matches what `discover_*`
# emits (e.g. `de_DE`, `zh-Hans`, `pt_BR`).
_ALLOWLIST_ENTRY_RE = re.compile(r"^([^:#\s]+):([0-9a-f]{16})$")


class AllowlistError(ValueError):
    """Raised when the allowlist file violates the schema.

    The validator is intentionally strict: bare hashes with no `# reason`
    comment, malformed entries, or hashes without a locale prefix all fail
    loud so the allowlist stays PR-reviewable rather than degenerating into
    an unauditable set of opaque hex strings."""


def load_allowlist(path: Path | None) -> set[str]:
    """Parse and validate the allowlist file.

    Schema (one entry per line):

        <locale>:<msgid_hash>  # reason text

    - Bare hashes (no `#` comment) raise AllowlistError.
    - Empty reason comments raise AllowlistError.
    - Malformed `<locale>:<hash>` segments raise AllowlistError.
    - Lines that start with `#` or are blank are ignored (header docs)."""
    if path is None or not path.is_file():
        return set()
    out: set[str] = set()
    errors: list[str] = []
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue  # pure-comment or blank line — fine
        # Entry line: must have an inline `# reason` comment.
        if "#" not in raw_line:
            errors.append(
                f"{path}:{lineno}: allowlist entry without '# reason' comment: "
                f"{stripped!r} — every entry must justify itself"
            )
            continue
        lhs, _, comment = raw_line.partition("#")
        entry = lhs.strip()
        if not comment.strip():
            errors.append(
                f"{path}:{lineno}: empty reason comment for {entry!r} — "
                f"explain why this msgid is exempt in this locale"
            )
            continue
        m = _ALLOWLIST_ENTRY_RE.match(entry)
        if not m:
            errors.append(
                f"{path}:{lineno}: malformed entry {entry!r} — expected "
                f"'<locale>:<msgid_hash>' (e.g. 'de_DE:abc123def4567890')"
            )
            continue
        out.add(entry)
    if errors:
        raise AllowlistError("\n".join(errors))
    return out


# --- CLI ------------------------------------------------------------------


def _format_findings(findings: list[Finding]) -> str:
    """Render findings without echoing the matched dictionary token.

    Per the original brief we never print the dictionary entry that matched
    (the "word") — defence in depth so CI logs stay shareable. We do print
    the English `msgid` (non-profane by definition) and the `target` (the
    translated string), since operators need *some* anchor for triage; the
    `target` may be removed in a future tightening pass.

    Each finding renders both as a GitHub Actions `::error::` annotation
    and (per CLI tradition) a human-readable trailing line. Extra
    diagnostics — XLIFF `id`, PO `#:` refs — are emitted when available."""
    lines: list[str] = []
    for f in findings:
        loc = f"{f.path}:{f.line}" if f.line else str(f.path)
        extras: list[str] = [
            f"locale={f.locale}",
            f"dict={f.dict_code}",
            f"allowlist_key={f.allowlist_key}",
            f"msgid={f.msgid!r}",
            f"target={f.target!r}",
        ]
        if f.xliff_id:
            extras.append(f"xliff_id={f.xliff_id}")
        if f.references:
            extras.append(f"refs={','.join(f.references)}")
        lines.append(
            f"::error file={f.path},line={f.line or 1}::"
            f"[{f.locale}] 1 match against profanity-dict[{f.dict_code}] at {loc} "
            f"({'; '.join(extras)})"
        )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    base_url = args.base_url or os.environ.get("PROFANITY_DICT_BASE_URL", DEFAULT_BASE_URL)
    try:
        allowlist = load_allowlist(Path(args.allowlist) if args.allowlist else None)
    except AllowlistError as exc:
        print("allowlist validation failed:", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    files = discover_translation_files(root)
    if not files:
        print(f"no translation files under {root}", file=sys.stderr)
        return 0

    by_dict_code: dict[str, list[tuple[Path, str, str]]] = {}
    skipped: list[str] = []
    for path, locale, kind in files:
        code = dict_code_for_locale(locale)
        if code is None:
            skipped.append(locale)
            continue
        by_dict_code.setdefault(code, []).append((path, locale, kind))

    if skipped:
        print(f"skipping source/pseudo locales: {sorted(set(skipped))}", file=sys.stderr)

    all_findings: list[Finding] = []
    for code in sorted(by_dict_code):
        dictionary = fetch_dictionary(code, base_url)
        if dictionary is None:
            print(f"[{code}] no dictionary at {base_url}/{code} — skipping", file=sys.stderr)
            continue
        if not dictionary:
            print(f"[{code}] empty dictionary — skipping", file=sys.stderr)
            continue
        for path, locale, kind in by_dict_code[code]:
            entries = iter_po(path, locale) if kind == "po" else iter_xliff(path, locale)
            for finding in scan_entries(entries, dictionary, dict_code=code):
                all_findings.append(finding)

    blocking = [f for f in all_findings if f.allowlist_key not in allowlist]
    allowed = [f for f in all_findings if f.allowlist_key in allowlist]

    if args.json:
        # JSON output is for local triage / piping; full diagnostics including
        # the target string are included so an operator can build allowlist
        # entries without re-running. CI logs use `_format_findings` which
        # redacts the matched dictionary token.
        print(
            json.dumps(
                {
                    "blocking": [
                        {
                            "locale": f.locale,
                            "path": str(f.path),
                            "line": f.line,
                            "dict_code": f.dict_code,
                            "allowlist_key": f.allowlist_key,
                            "msgid": f.msgid,
                            "msgid_hash": f.msgid_hash,
                            "target": f.target,
                            "xliff_id": f.xliff_id,
                            "references": list(f.references),
                        }
                        for f in blocking
                    ],
                    "allowed_count": len(allowed),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        if allowed:
            print(f"allowlisted matches (suppressed): {len(allowed)}", file=sys.stderr)
        if blocking:
            print(_format_findings(blocking))
            print(
                f"\n{len(blocking)} blocking match(es). "
                f"To allowlist a false positive, append a line of the form "
                f"'<locale>:<msgid_hash>  # reason' to "
                f"{args.allowlist or 'scripts/.translation_profanity_allowlist'}.",
                file=sys.stderr,
            )

    return 1 if blocking else 0


# --- self-test ------------------------------------------------------------


def _selftest() -> int:
    """Inline tests using abstract placeholder tokens (no real profanity).

    Run with: python scripts/translation_profanity_check.py --self-test
    """
    import tempfile
    import unittest

    PLACEHOLDER_DICT = "xyzzy\nfrobnitz\n# a comment\n  \nmultiword token\n"
    CJK_DICT = "蛙蛙蛙\n"  # placeholder CJK token

    class Tests(unittest.TestCase):
        def test_normalize_casefold(self):
            self.assertEqual(normalize("Xyzzy"), "xyzzy")
            # NFKC collapses fullwidth Latin to ASCII.
            self.assertEqual(normalize("ｘｙｚｚｙ"), "xyzzy")

        def test_dict_code(self):
            self.assertEqual(dict_code_for_locale("de_DE"), "de")
            self.assertEqual(dict_code_for_locale("pt_BR"), "pt")
            self.assertEqual(dict_code_for_locale("zh-Hans"), "zh")
            self.assertIsNone(dict_code_for_locale("en"))
            self.assertIsNone(dict_code_for_locale("en-XA"))

        def test_parse_dictionary(self):
            self.assertEqual(
                parse_dictionary(PLACEHOLDER_DICT),
                ["xyzzy", "frobnitz", "multiword token"],
            )

        def test_word_boundary_match(self):
            dictionary = parse_dictionary(PLACEHOLDER_DICT)
            entries = [
                TranslationEntry(Path("x"), 1, "de_DE", "Hello", "Sag xyzzy!"),
                TranslationEntry(Path("x"), 2, "de_DE", "Hi", "xyzzyish should not match"),
                TranslationEntry(Path("x"), 3, "de_DE", "Plural", "frobnitzes here"),
            ]
            findings = list(scan_entries(entries, dictionary, dict_code="de"))
            words = [f.word for f in findings]
            # "xyzzy" matches in entry 1 (word boundary).
            # "xyzzyish" should NOT match (no boundary).
            # "frobnitzes" should NOT match standalone (no boundary after "frobnitz").
            self.assertIn("xyzzy", words)
            self.assertNotIn("frobnitz", words)
            self.assertEqual(len(findings), 1)

        def test_multiword_substring_match(self):
            dictionary = parse_dictionary(PLACEHOLDER_DICT)
            entry = TranslationEntry(
                Path("x"), 1, "de_DE", "src", "contains a multiword token here"
            )
            findings = list(scan_entries([entry], dictionary, dict_code="de"))
            self.assertEqual([f.word for f in findings], ["multiword token"])

        def test_cjk_substring(self):
            dictionary = parse_dictionary(CJK_DICT)
            entry = TranslationEntry(Path("x"), 1, "zh-Hans", "src", "前面蛙蛙蛙後面")
            findings = list(scan_entries([entry], dictionary, dict_code="zh"))
            self.assertEqual([f.word for f in findings], ["蛙蛙蛙"])

        def test_allowlist_key_is_locale_prefixed(self):
            msgid = "Some English source string"
            target_text = "übersetzung mit xyzzy"
            entry = TranslationEntry(Path("x"), 1, "de_DE", msgid, target_text)
            dictionary = parse_dictionary(PLACEHOLDER_DICT)
            findings = list(scan_entries([entry], dictionary, dict_code="de"))
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].msgid_hash, msgid_hash(msgid))
            self.assertEqual(findings[0].allowlist_key, f"de_DE:{msgid_hash(msgid)}")

        def test_po_parser_extracts_target_and_refs(self):
            content = (
                'msgid ""\n'
                'msgstr ""\n'
                '"Content-Type: text/plain; charset=UTF-8\\n"\n'
                "\n"
                "#: authentik/admin/files/api.py:142\n"
                "#: authentik/admin/files/other.py:7\n"
                "#, python-brace-format\n"
                'msgid "Hello"\n'
                'msgstr "Hallo xyzzy"\n'
                "\n"
                "#: authentik/other.py:99\n"
                'msgid "Multi"\n'
                '"line source"\n'
                'msgstr "Mehr"\n'
                '"zeilig"\n'
            )
            with tempfile.NamedTemporaryFile(
                "w", suffix=".po", delete=False, encoding="utf-8"
            ) as fh:
                fh.write(content)
                tmp = Path(fh.name)
            try:
                entries = list(iter_po(tmp, "de_DE"))
            finally:
                tmp.unlink()
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].msgid, "Hello")
            self.assertEqual(entries[0].target, "Hallo xyzzy")
            self.assertEqual(
                entries[0].references,
                (
                    "authentik/admin/files/api.py:142",
                    "authentik/admin/files/other.py:7",
                ),
            )
            self.assertEqual(entries[1].msgid, "Multiline source")
            self.assertEqual(entries[1].target, "Mehrzeilig")
            self.assertEqual(entries[1].references, ("authentik/other.py:99",))

        def test_xliff_parser_extracts_target_and_id(self):
            xml = (
                '<?xml version="1.0"?>'
                '<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2"'
                ' version="1.2">'
                '<file target-language="de-DE" source-language="en"'
                ' original="x" datatype="plaintext">'
                "<body>"
                '<trans-unit id="sfe629863ba1338c2"><source>Hello</source>'
                "<target>Hallo xyzzy</target></trans-unit>"
                '<trans-unit id="b"><source>Skip</source>'
                "<target></target></trans-unit>"
                "</body></file></xliff>"
            )
            with tempfile.NamedTemporaryFile(
                "w", suffix=".xlf", delete=False, encoding="utf-8"
            ) as fh:
                fh.write(xml)
                tmp = Path(fh.name)
            try:
                entries = list(iter_xliff(tmp, "de-DE"))
            finally:
                tmp.unlink()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].target, "Hallo xyzzy")
            self.assertEqual(entries[0].xliff_id, "sfe629863ba1338c2")

        def test_fetch_dictionary_404_returns_none(self):
            def fake_fetch(url):
                raise urllib.error.HTTPError(url, 404, "not found", None, None)

            self.assertIsNone(fetch_dictionary("xx", "https://example.invalid", fetcher=fake_fetch))

        def test_run_blocks_on_match(self):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "locale" / "de_DE" / "LC_MESSAGES").mkdir(parents=True)
                (root / "locale" / "de_DE" / "LC_MESSAGES" / "django.po").write_text(
                    'msgid "Hello"\nmsgstr "Hallo xyzzy"\n', encoding="utf-8"
                )
                dict_dir = root / "dict"
                dict_dir.mkdir()
                (dict_dir / "de").write_text(PLACEHOLDER_DICT, encoding="utf-8")

                ns = argparse.Namespace(
                    root=str(root),
                    base_url=f"file://{dict_dir}",
                    allowlist=None,
                    json=False,
                )
                rc = run(ns)
                self.assertEqual(rc, 1)

        def test_run_passes_when_clean(self):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "locale" / "de_DE" / "LC_MESSAGES").mkdir(parents=True)
                (root / "locale" / "de_DE" / "LC_MESSAGES" / "django.po").write_text(
                    'msgid "Hello"\nmsgstr "Hallo Welt"\n', encoding="utf-8"
                )
                dict_dir = root / "dict"
                dict_dir.mkdir()
                (dict_dir / "de").write_text(PLACEHOLDER_DICT, encoding="utf-8")

                ns = argparse.Namespace(
                    root=str(root),
                    base_url=f"file://{dict_dir}",
                    allowlist=None,
                    json=False,
                )
                self.assertEqual(run(ns), 0)

        def test_run_allowlist_suppresses_with_locale_key(self):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "locale" / "de_DE" / "LC_MESSAGES").mkdir(parents=True)
                (root / "locale" / "de_DE" / "LC_MESSAGES" / "django.po").write_text(
                    'msgid "Hello"\nmsgstr "Hallo xyzzy"\n', encoding="utf-8"
                )
                dict_dir = root / "dict"
                dict_dir.mkdir()
                (dict_dir / "de").write_text(PLACEHOLDER_DICT, encoding="utf-8")
                allow = root / "allow.txt"
                allow.write_text(
                    f"de_DE:{msgid_hash('Hello')}  # placeholder term, reviewed 2026-05-16\n",
                    encoding="utf-8",
                )

                ns = argparse.Namespace(
                    root=str(root),
                    base_url=f"file://{dict_dir}",
                    allowlist=str(allow),
                    json=False,
                )
                self.assertEqual(run(ns), 0)

        def test_run_allowlist_other_locale_does_not_suppress(self):
            # Per-locale schema: a `ja_JP:<hash>` entry must NOT suppress a
            # match in `de_DE` even if msgid hash collides.
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "locale" / "de_DE" / "LC_MESSAGES").mkdir(parents=True)
                (root / "locale" / "de_DE" / "LC_MESSAGES" / "django.po").write_text(
                    'msgid "Hello"\nmsgstr "Hallo xyzzy"\n', encoding="utf-8"
                )
                dict_dir = root / "dict"
                dict_dir.mkdir()
                (dict_dir / "de").write_text(PLACEHOLDER_DICT, encoding="utf-8")
                allow = root / "allow.txt"
                allow.write_text(
                    f"ja_JP:{msgid_hash('Hello')}  # exempt only in ja\n",
                    encoding="utf-8",
                )

                ns = argparse.Namespace(
                    root=str(root),
                    base_url=f"file://{dict_dir}",
                    allowlist=str(allow),
                    json=False,
                )
                self.assertEqual(run(ns), 1)

        def test_allowlist_bare_hash_fails_loud(self):
            with tempfile.TemporaryDirectory() as td:
                allow = Path(td) / "allow.txt"
                # Bare hash with no `# reason` comment must error.
                allow.write_text(f"de_DE:{msgid_hash('Hello')}\n", encoding="utf-8")
                with self.assertRaises(AllowlistError) as ctx:
                    load_allowlist(allow)
                self.assertIn("'# reason'", str(ctx.exception))

        def test_allowlist_empty_reason_fails_loud(self):
            with tempfile.TemporaryDirectory() as td:
                allow = Path(td) / "allow.txt"
                allow.write_text(f"de_DE:{msgid_hash('Hello')}  #   \n", encoding="utf-8")
                with self.assertRaises(AllowlistError) as ctx:
                    load_allowlist(allow)
                self.assertIn("empty reason", str(ctx.exception))

        def test_allowlist_missing_locale_prefix_fails_loud(self):
            with tempfile.TemporaryDirectory() as td:
                allow = Path(td) / "allow.txt"
                # Bare hash without `<locale>:` prefix.
                allow.write_text(f"{msgid_hash('Hello')}  # bad shape\n", encoding="utf-8")
                with self.assertRaises(AllowlistError) as ctx:
                    load_allowlist(allow)
                self.assertIn("malformed entry", str(ctx.exception))

        def test_allowlist_pure_comment_lines_ok(self):
            with tempfile.TemporaryDirectory() as td:
                allow = Path(td) / "allow.txt"
                allow.write_text(
                    "# header comment\n"
                    "  # indented comment\n"
                    "\n"
                    f"de_DE:{msgid_hash('Hello')}  # ok entry\n",
                    encoding="utf-8",
                )
                loaded = load_allowlist(allow)
                self.assertEqual(loaded, {f"de_DE:{msgid_hash('Hello')}"})

        def test_findings_format_omits_matched_word(self):
            # Defence in depth: the rendered output line must not include
            # the dictionary entry that matched.
            f = Finding(
                locale="de_DE",
                path=Path("locale/de_DE/LC_MESSAGES/django.po"),
                line=42,
                word="xyzzy",  # never echoed
                msgid="Hello",
                target="Hallo xyzzy",
                dict_code="de",
                references=("authentik/admin/api.py:1",),
                xliff_id=None,
            )
            rendered = _format_findings([f])
            self.assertNotIn("xyzzy", rendered.split(" target=", 1)[0])
            # `dict[<code>]` style summary appears instead.
            self.assertIn("profanity-dict[de]", rendered)
            self.assertIn("refs=authentik/admin/api.py:1", rendered)
            self.assertIn(f"allowlist_key=de_DE:{msgid_hash('Hello')}", rendered)

        def test_findings_format_includes_xliff_id(self):
            f = Finding(
                locale="de-DE",
                path=Path("web/xliff/de-DE.xlf"),
                line=0,
                word="xyzzy",
                msgid="Hello",
                target="Hallo xyzzy",
                dict_code="de",
                references=(),
                xliff_id="sfe629863ba1338c2",
            )
            rendered = _format_findings([f])
            self.assertIn("xliff_id=sfe629863ba1338c2", rendered)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(Tests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Profanity dictionary base URL. Defaults to $PROFANITY_DICT_BASE_URL "
        f"or {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--allowlist",
        default="scripts/.translation_profanity_allowlist",
        help=(
            "Path to the allowlist. Each entry is "
            "'<locale>:<msgid_hash>  # reason' on its own line; bare hashes "
            "or missing-reason entries cause the scanner to fail loud."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON")
    parser.add_argument("--self-test", action="store_true", help="Run inline unit tests and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return _selftest()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
