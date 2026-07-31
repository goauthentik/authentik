"""Tests for the XLIFF target merge."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from authentik.lib.xliff import drop_invalid_targets, merge_targets, read_targets

HEADER = (
    '<?xml version="1.0"?><xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" '
    'version="1.2">\n<file target-language="{lang}" source-language="en" '
    'original="lit-localize-inputs" datatype="plaintext">\n<body>\n'
)
FOOTER = "</body>\n</file>\n</xliff>\n"


def document(lang: str, units: str) -> str:
    return HEADER.format(lang=lang) + units + FOOTER


def unit(identifier: str, source: str, target: str | None = None) -> str:
    body = f'<trans-unit id="{identifier}">\n  <source>{source}</source>\n'
    if target is not None:
        body += f"  <target>{target}</target>\n"
    return body + "</trans-unit>\n"


class TestReadTargets(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name: str, body: str) -> Path:
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_reads_populated_targets(self):
        path = self.write(
            "de.xlf",
            document("de-DE", unit("a", "One", "Eins") + unit("b", "Two")),
        )
        self.assertEqual(read_targets(path), {"a": "<target>Eins</target>"})

    def test_skips_empty_target(self):
        path = self.write("de.xlf", document("de-DE", unit("a", "One", "")))
        self.assertEqual(read_targets(path), {})

    def test_keeps_placeholder_only_target(self):
        """A target that is only a placeholder is still a real translation."""
        path = self.write(
            "de.xlf",
            document("de-DE", unit("a", "x", '<x id="0" equiv-text="${n}"/>')),
        )
        self.assertIn("a", read_targets(path))


class TestDropInvalidTargets(TestCase):
    """Targets that cannot render are removed so the rest of a language ships."""

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name: str, body: str) -> Path:
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_drops_target_missing_a_placeholder(self):
        path = self.write(
            "hr.xlf",
            document(
                "hr-HR",
                unit("a", 'Version <x id="0" equiv-text="${v}"/>', "Verzija"),
            ),
        )

        self.assertEqual(drop_invalid_targets(path), 1)

        body = path.read_text(encoding="utf-8")
        self.assertNotIn("<target>", body)
        self.assertIn("<source>", body)

    def test_keeps_valid_targets(self):
        source = 'Version <x id="0" equiv-text="${v}"/>'
        path = self.write(
            "hr.xlf",
            document("hr-HR", unit("a", source, 'Verzija <x id="0" equiv-text="${v}"/>')),
        )

        self.assertEqual(drop_invalid_targets(path), 0)
        self.assertIn("<target>", path.read_text(encoding="utf-8"))

    def test_leaves_untranslated_units_alone(self):
        path = self.write("hr.xlf", document("hr-HR", unit("a", "Plain")))
        self.assertEqual(drop_invalid_targets(path), 0)


class TestMergeTargets(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name: str, body: str) -> Path:
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_fills_missing_target(self):
        canonical = self.write("c.xlf", document("de-DE", unit("a", "One")))
        donor = self.write("d.xlf", document("de-DE", unit("a", "One", "Eins")))

        result = merge_targets(canonical, donor)

        self.assertEqual(result.filled, 1)
        self.assertEqual(result.replaced, 0)
        self.assertIn("<target>Eins</target>", canonical.read_text(encoding="utf-8"))

    def test_donor_wins_conflict(self):
        canonical = self.write("c.xlf", document("de-DE", unit("a", "One", "Alt")))
        donor = self.write("d.xlf", document("de-DE", unit("a", "One", "Neu")))

        result = merge_targets(canonical, donor)

        self.assertEqual(result.replaced, 1)
        body = canonical.read_text(encoding="utf-8")
        self.assertIn("<target>Neu</target>", body)
        self.assertNotIn("Alt", body)

    def test_keeps_target_donor_lacks(self):
        """Work that exists only in the canonical file survives."""
        canonical = self.write("c.xlf", document("de-DE", unit("a", "One", "Eins")))
        donor = self.write("d.xlf", document("de-DE", unit("a", "One")))

        result = merge_targets(canonical, donor)

        self.assertEqual(result.changed, 0)
        self.assertEqual(result.kept, 1)
        self.assertIn("<target>Eins</target>", canonical.read_text(encoding="utf-8"))

    def test_canonical_supplies_the_skeleton(self):
        """Units only the donor knows about are dropped."""
        canonical = self.write("c.xlf", document("de-DE", unit("a", "One")))
        donor = self.write(
            "d.xlf",
            document("de-DE", unit("a", "One", "Eins") + unit("gone", "Old", "Alt")),
        )

        merge_targets(canonical, donor)

        body = canonical.read_text(encoding="utf-8")
        self.assertIn('id="a"', body)
        self.assertNotIn("gone", body)

    def test_preserves_placeholders(self):
        placeholder = '<x id="0" equiv-text="${name}"/> folgt'
        source = '<x id="0" equiv-text="${name}"/> follows'
        canonical = self.write("c.xlf", document("de-DE", unit("a", source)))
        donor = self.write("d.xlf", document("de-DE", unit("a", source, placeholder)))

        merge_targets(canonical, donor)

        self.assertIn(placeholder, canonical.read_text(encoding="utf-8"))

    def test_replaces_empty_target_in_place(self):
        canonical = self.write("c.xlf", document("de-DE", unit("a", "One", "")))
        donor = self.write("d.xlf", document("de-DE", unit("a", "One", "Eins")))

        result = merge_targets(canonical, donor)

        self.assertEqual(result.filled, 1)
        body = canonical.read_text(encoding="utf-8")
        self.assertIn("<target>Eins</target>", body)
        self.assertNotIn("<target></target>", body)

    def test_leaves_surrounding_formatting_alone(self):
        """Only the target changes; the rest of the file is byte-identical."""
        canonical = self.write(
            "c.xlf",
            document("de-DE", unit("a", "One") + unit("b", "Two", "Zwei")),
        )
        before = canonical.read_text(encoding="utf-8")
        donor = self.write("d.xlf", document("de-DE", unit("a", "One", "Eins")))

        merge_targets(canonical, donor)

        after = canonical.read_text(encoding="utf-8")
        self.assertEqual(
            before.replace("  <source>One</source>\n", "MARK"),
            after.replace("  <source>One</source>\n  <target>Eins</target>\n", "MARK"),
        )

    def test_keeps_canonical_when_only_markup_differs(self):
        """A donor saying the same thing does not get to rewrite the file.

        The canonical file holds the newer skeleton, so its placeholder
        metadata and line wrapping are the ones worth keeping.
        """
        canonical = self.write(
            "c.xlf",
            document(
                "de-DE",
                unit(
                    "a",
                    'Rule <x id="0" equiv-text="${item.name}"/>',
                    'Regel\n        <x id="0" equiv-text="${item.name}"/>',
                ),
            ),
        )
        donor = self.write(
            "d.xlf",
            document(
                "de-DE",
                unit(
                    "a",
                    'Rule <x id="0" equiv-text="${item.name}"/>',
                    'Regel <x id="0" equiv-text="${old}"/>',
                ),
            ),
        )

        result = merge_targets(canonical, donor)

        self.assertEqual(result.changed, 0)
        body = canonical.read_text(encoding="utf-8")
        self.assertIn("${item.name}", body)
        self.assertNotIn("${old}", body)

    def test_entity_escaping_is_not_a_translation_change(self):
        """`&quot;` and a literal quote say the same thing."""
        canonical = self.write("c.xlf", document("de-DE", unit("a", "x", 'Sortiere nach "Name"')))
        donor = self.write(
            "d.xlf",
            document("de-DE", unit("a", "x", "Sortiere nach &quot;Name&quot;")),
        )

        result = merge_targets(canonical, donor)

        self.assertEqual(result.changed, 0)
        self.assertIn('"Name"', canonical.read_text(encoding="utf-8"))

    def test_still_replaces_when_wording_differs(self):
        source = 'x <x id="0" equiv-text="${n}"/>'
        canonical = self.write(
            "c.xlf", document("de-DE", unit("a", source, 'Alt <x id="0" equiv-text="${n}"/>'))
        )
        donor = self.write(
            "d.xlf", document("de-DE", unit("a", source, 'Neu <x id="0" equiv-text="${n}"/>'))
        )

        result = merge_targets(canonical, donor)

        self.assertEqual(result.replaced, 1)
        self.assertIn("Neu", canonical.read_text(encoding="utf-8"))

    def test_rejects_donor_missing_a_placeholder(self):
        """A donor that drops a placeholder the source requires is refused.

        lit-localize fails the build on a placeholder mismatch, and the dropped
        substitution would not render at runtime. An older donor predating the
        placeholder must not overwrite a correct translation.
        """
        source = 'Imported <x id="0" equiv-text="${res.count}"/> devices'
        canonical = self.write(
            "c.xlf",
            document(
                "pt-BR",
                unit("a", source, 'Importados <x id="0" equiv-text="${res.count}"/>.'),
            ),
        )
        donor = self.write("d.xlf", document("pt-BR", unit("a", source, "Importados.")))

        result = merge_targets(canonical, donor)

        self.assertEqual(result.rejected, 1)
        self.assertEqual(result.changed, 0)
        self.assertIn("${res.count}", canonical.read_text(encoding="utf-8"))

    def test_rejects_donor_carrying_a_removed_placeholder(self):
        """The mismatch is refused in both directions."""
        canonical = self.write("c.xlf", document("de-DE", unit("a", "Done")))
        donor = self.write(
            "d.xlf",
            document("de-DE", unit("a", "Done", 'Fertig <x id="0" equiv-text="${n}"/>')),
        )

        result = merge_targets(canonical, donor)

        self.assertEqual(result.rejected, 1)
        self.assertEqual(result.filled, 0)

    def test_accepts_matching_placeholders(self):
        source = 'Hello <x id="0" equiv-text="${name}"/>'
        canonical = self.write("c.xlf", document("de-DE", unit("a", source)))
        donor = self.write(
            "d.xlf",
            document("de-DE", unit("a", source, 'Hallo <x id="0" equiv-text="${name}"/>')),
        )

        result = merge_targets(canonical, donor)

        self.assertEqual(result.rejected, 0)
        self.assertEqual(result.filled, 1)

    def test_write_false_leaves_file_untouched(self):
        canonical = self.write("c.xlf", document("de-DE", unit("a", "One")))
        donor = self.write("d.xlf", document("de-DE", unit("a", "One", "Eins")))
        before = canonical.read_text(encoding="utf-8")

        result = merge_targets(canonical, donor, write=False)

        self.assertEqual(result.filled, 1)
        self.assertEqual(canonical.read_text(encoding="utf-8"), before)
