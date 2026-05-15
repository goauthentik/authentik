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


def iter_po(path: Path, locale: str) -> Iterator[TranslationEntry]:
    """Minimal PO reader: yields (msgid, msgstr) pairs with line numbers.

    Handles multi-line continuation strings and fuzzy/obsolete entries (we
    include fuzzy entries — they still ship to users — but skip obsolete
    `#~` entries)."""
    msgid_parts: list[str] = []
    msgstr_parts: list[str] = []
    state: str | None = None  # None | "msgid" | "msgstr"
    entry_line = 0

    def flush() -> Iterator[TranslationEntry]:
        if msgid_parts or msgstr_parts:
            msgid = "".join(msgid_parts)
            target = "".join(msgstr_parts)
            if msgid and target:  # skip the empty header entry
                yield TranslationEntry(path, entry_line, locale, msgid, target)

    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.rstrip("\n")
            stripped = line.lstrip()
            if stripped.startswith("#~"):
                # Obsolete entry — drop pending and skip.
                msgid_parts, msgstr_parts, state = [], [], None
                continue
            if not stripped or stripped.startswith("#"):
                if not stripped and state is not None:
                    # Blank line terminates an entry.
                    yield from flush()
                    msgid_parts, msgstr_parts, state = [], [], None
                continue
            if stripped.startswith("msgid "):
                yield from flush()
                msgid_parts = [_po_unquote(stripped[len("msgid ") :])]
                msgstr_parts = []
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
    """Yields trans-units that have a non-empty <target>."""
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
        msgid = "".join(src_el.itertext()) if src_el is not None else unit.get("id", "")
        # XLIFF ElementTree doesn't expose line numbers natively; report 0 to
        # mean "see file". Acceptable trade-off vs. pulling in lxml.
        yield TranslationEntry(path, 0, locale, msgid, target)


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
    word: str
    msgid: str
    target: str

    @property
    def msgid_hash(self) -> str:
        return msgid_hash(self.msgid)


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
                )


# --- allowlist ------------------------------------------------------------


def load_allowlist(path: Path | None) -> set[str]:
    if path is None or not path.is_file():
        return set()
    out: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        entry = raw_line.split("#", 1)[0].strip()
        if entry:
            out.add(entry)
    return out


# --- CLI ------------------------------------------------------------------


def _format_findings(findings: list[Finding]) -> str:
    lines = []
    for f in findings:
        loc = f"{f.path}:{f.line}" if f.line else str(f.path)
        lines.append(
            f"::error file={f.path},line={f.line or 1}::"
            f"[{f.locale}] profanity match {f.word!r} at {loc} "
            f"(msgid_hash={f.msgid_hash}, msgid={f.msgid!r}, target={f.target!r})"
        )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    base_url = args.base_url or os.environ.get("PROFANITY_DICT_BASE_URL", DEFAULT_BASE_URL)
    allowlist = load_allowlist(Path(args.allowlist) if args.allowlist else None)

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
            for finding in scan_entries(entries, dictionary):
                all_findings.append(finding)

    blocking = [f for f in all_findings if f.msgid_hash not in allowlist]
    allowed = [f for f in all_findings if f.msgid_hash in allowlist]

    if args.json:
        print(
            json.dumps(
                {
                    "blocking": [
                        {
                            "locale": f.locale,
                            "path": str(f.path),
                            "line": f.line,
                            "word": f.word,
                            "msgid_hash": f.msgid_hash,
                        }
                        for f in blocking
                    ],
                    "allowed_count": len(allowed),
                },
                indent=2,
            )
        )
    else:
        if allowed:
            print(f"allowlisted matches (suppressed): {len(allowed)}", file=sys.stderr)
        if blocking:
            print(_format_findings(blocking))
            print(
                f"\n{len(blocking)} blocking match(es). "
                f"To allowlist a false positive, append its msgid_hash to "
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
            findings = list(scan_entries(entries, dictionary))
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
            findings = list(scan_entries([entry], dictionary))
            self.assertEqual([f.word for f in findings], ["multiword token"])

        def test_cjk_substring(self):
            dictionary = parse_dictionary(CJK_DICT)
            entry = TranslationEntry(Path("x"), 1, "zh-Hans", "src", "前面蛙蛙蛙後面")
            findings = list(scan_entries([entry], dictionary))
            self.assertEqual([f.word for f in findings], ["蛙蛙蛙"])

        def test_allowlist_by_hash(self):
            msgid = "Some English source string"
            target_text = "übersetzung mit xyzzy"
            entry = TranslationEntry(Path("x"), 1, "de_DE", msgid, target_text)
            dictionary = parse_dictionary(PLACEHOLDER_DICT)
            findings = list(scan_entries([entry], dictionary))
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].msgid_hash, msgid_hash(msgid))

        def test_po_parser_extracts_target(self):
            content = (
                'msgid ""\n'
                'msgstr ""\n'
                '"Content-Type: text/plain; charset=UTF-8\\n"\n'
                "\n"
                'msgid "Hello"\n'
                'msgstr "Hallo xyzzy"\n'
                "\n"
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
            self.assertEqual(entries[1].msgid, "Multiline source")
            self.assertEqual(entries[1].target, "Mehrzeilig")

        def test_xliff_parser_extracts_target(self):
            xml = (
                '<?xml version="1.0"?>'
                '<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2"'
                ' version="1.2">'
                '<file target-language="de-DE" source-language="en"'
                ' original="x" datatype="plaintext">'
                "<body>"
                '<trans-unit id="a"><source>Hello</source>'
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

        def test_run_allowlist_suppresses(self):
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
                allow.write_text(msgid_hash("Hello") + "\n", encoding="utf-8")

                ns = argparse.Namespace(
                    root=str(root),
                    base_url=f"file://{dict_dir}",
                    allowlist=str(allow),
                    json=False,
                )
                self.assertEqual(run(ns), 0)

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
        help="Path to msgid-hash allowlist (one hash per line, '#' comments).",
    )
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON")
    parser.add_argument("--self-test", action="store_true", help="Run inline unit tests and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return _selftest()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
