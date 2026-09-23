"""Test blueprints v1 tasks"""

from hashlib import sha512
from pathlib import Path
from tempfile import NamedTemporaryFile, mkdtemp

from django.test import TransactionTestCase
from yaml import dump

from authentik.blueprints.models import BlueprintInstance, BlueprintInstanceStatus
from authentik.blueprints.v1.tasks import apply_blueprint, blueprints_discovery, blueprints_find
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id

TMP = mkdtemp("authentik-blueprints")


class TestBlueprintsV1Tasks(TransactionTestCase):
    """Test Blueprints v1 Tasks"""

    @CONFIG.patch("blueprints_dir", TMP)
    def test_invalid_file_syntax(self):
        """Test syntactically invalid file"""
        with NamedTemporaryFile(suffix=".yaml", dir=TMP) as file:
            file.write(b"{")
            file.flush()
            blueprints = blueprints_find()
            self.assertEqual(blueprints, [])

    @CONFIG.patch("blueprints_dir", TMP)
    def test_invalid_file_version(self):
        """Test invalid file"""
        with NamedTemporaryFile(suffix=".yaml", dir=TMP) as file:
            file.write(b"version: 2")
            file.flush()
            blueprints = blueprints_find()
            self.assertEqual(blueprints, [])

    @CONFIG.patch("blueprints_dir", TMP)
    def test_valid(self):
        """Test valid file"""
        blueprint_id = generate_id()
        with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
            file.write(
                dump(
                    {
                        "version": 1,
                        "entries": [],
                        "metadata": {
                            "name": blueprint_id,
                        },
                    }
                )
            )
            file.seek(0)
            file_hash = sha512(file.read().encode()).hexdigest()
            file.flush()
            blueprints_discovery.send()
            instance = BlueprintInstance.objects.filter(name=blueprint_id).first()
            self.assertEqual(instance.last_applied_hash, file_hash)
            self.assertEqual(
                instance.metadata,
                {
                    "name": blueprint_id,
                    "labels": {},
                },
            )

    @CONFIG.patch("blueprints_dir", TMP)
    def test_valid_updated(self):
        """Test valid file"""
        BlueprintInstance.objects.filter(name="foo").delete()
        with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
            file.write(
                dump(
                    {
                        "version": 1,
                        "entries": [],
                        "metadata": {
                            "name": "foo",
                        },
                    }
                )
            )
            file.flush()
            blueprints_discovery.send()
            blueprint = BlueprintInstance.objects.filter(name="foo").first()
            self.assertEqual(
                blueprint.last_applied_hash,
                (
                    "b86ec439b3857350714f070d2833490e736d9155d3d97b2cac13f3b352223e5a"
                    "1adbf8ec56fa616d46090cc4773ff9e46c4e509fde96b97de87dd21fa329ca1a"
                ),
            )
            self.assertEqual(blueprint.metadata, {"labels": {}, "name": "foo"})
            file.write(
                dump(
                    {
                        "version": 1,
                        "entries": [],
                        "metadata": {
                            "name": "foo",
                            "labels": {
                                "foo": "bar",
                            },
                        },
                    }
                )
            )
            file.flush()
            blueprints_discovery.send()
            blueprint.refresh_from_db()
            self.assertEqual(
                blueprint.last_applied_hash,
                (
                    "87b68b10131d2c9751ed308bba38f04734b9e2cdf8532ed617bc52979b063c49"
                    "2564f33f3d20ab9d5f0fd9e6eb77a13942e060199f147789cb7afab9690e72b5"
                ),
            )
            self.assertEqual(
                blueprint.metadata,
                {
                    "name": "foo",
                    "labels": {"foo": "bar"},
                },
            )

    @CONFIG.patch("blueprints_dir", TMP)
    def test_valid_disabled(self):
        """Test valid file"""
        with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
            file.write(
                dump(
                    {
                        "version": 1,
                        "entries": [],
                    }
                )
            )
            file.flush()
            instance: BlueprintInstance = BlueprintInstance.objects.create(
                name=generate_id(),
                path=file.name,
                enabled=False,
                status=BlueprintInstanceStatus.UNKNOWN,
            )
            instance.refresh_from_db()
            self.assertEqual(instance.last_applied_hash, "")
            self.assertEqual(
                instance.status,
                BlueprintInstanceStatus.UNKNOWN,
            )
            apply_blueprint.send(instance.pk).get_result(block=True)
            instance.refresh_from_db()
            self.assertEqual(instance.last_applied_hash, "")
            self.assertEqual(
                instance.status,
                BlueprintInstanceStatus.UNKNOWN,
            )

    @CONFIG.patch("blueprints_dir", TMP)
    def test_valid_crlf(self):
        """Test discovered hash matches the applied hash for a file with CRLF line endings"""
        blueprint_id = generate_id()
        with NamedTemporaryFile(suffix=".yaml", dir=TMP) as file:
            file.write(
                f"version: 1\r\nentries: []\r\nmetadata:\r\n  name: {blueprint_id}\r\n".encode()
            )
            file.flush()
            file_hash = sha512(Path(file.name).read_text(encoding="utf-8").encode()).hexdigest()
            for _ in range(2):
                blueprints_discovery.send()
                instance = BlueprintInstance.objects.filter(name=blueprint_id).first()
                self.assertEqual(instance.status, BlueprintInstanceStatus.SUCCESSFUL)
                found = next(
                    found for found in blueprints_find() if found.path == Path(file.name).name
                )
                self.assertEqual(found.hash, file_hash)
                self.assertEqual(instance.last_applied_hash, found.hash)
            file.seek(0)
            self.assertIn(b"\r\n", file.read())

    def write_blueprint(self, file, value: str):
        file.seek(0)
        file.truncate()
        file.write(f"version: 1\nentries: []\ncontext:\n  secret: {value}\n")
        file.flush()
        return next(found for found in blueprints_find() if found.path == Path(file.name).name).hash

    def write_secret(self, file, value: str):
        file.seek(0)
        file.truncate()
        file.write(value)
        file.flush()

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_content_changed(self):
        """Test hash changes when the contents of a referenced `!File` change"""
        with NamedTemporaryFile(mode="w+", dir=TMP) as secret:
            for label, reference in (
                ("direct", f"!File {secret.name}"),
                ("argument of another tag", f'!Format ["client-%s", !File {secret.name}]'),
                ("reached through a cycle", f"&anchor [*anchor, !File {secret.name}]"),
                ("reached through an alias", f"&anchor [!File {secret.name}]\n  other: *anchor"),
            ):
                with (
                    self.subTest(label),
                    NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file,
                ):
                    self.write_secret(secret, "initial")
                    before = self.write_blueprint(file, reference)
                    self.write_secret(secret, "rotated")
                    self.assertNotEqual(before, self.write_blueprint(file, reference))

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_created(self):
        """Test hash changes when a referenced `!File` that was missing appears"""
        with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
            secret_path = Path(TMP) / generate_id()
            reference = f"!File {secret_path}"
            before = self.write_blueprint(file, reference)
            secret_path.write_text("created")
            try:
                after = self.write_blueprint(file, reference)
            finally:
                secret_path.unlink()
            self.assertNotEqual(before, after)

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_removed(self):
        """Test hash changes when a referenced `!File` that existed disappears"""
        with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
            secret_path = Path(TMP) / generate_id()
            secret_path.write_text("present")
            reference = f"!File {secret_path}"
            try:
                before = self.write_blueprint(file, reference)
            finally:
                secret_path.unlink()
            self.assertNotEqual(before, self.write_blueprint(file, reference))

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_contents_swapped(self):
        """Test hash changes when two referenced `!File`s exchange their contents"""
        with (
            NamedTemporaryFile(mode="w+", dir=TMP) as first,
            NamedTemporaryFile(mode="w+", dir=TMP) as second,
        ):
            self.write_secret(first, "alpha")
            self.write_secret(second, "beta")
            with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
                reference = f"[!File {first.name}, !File {second.name}]"
                before = self.write_blueprint(file, reference)
                self.write_secret(first, "beta")
                self.write_secret(second, "alpha")
                self.assertNotEqual(before, self.write_blueprint(file, reference))

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_hashed_once_per_route(self):
        """Test a referenced `!File` is folded into the hash once for each route to it"""
        with NamedTemporaryFile(mode="w+", dir=TMP) as secret:
            self.write_secret(secret, "initial")
            for label, reference, routes in (
                ("cycle", f"&anchor [*anchor, !File {secret.name}]", 1),
                ("alias", f"&anchor [!File {secret.name}]\n  other: *anchor", 2),
            ):
                with (
                    self.subTest(label),
                    NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file,
                ):
                    content = f"version: 1\nentries: []\ncontext:\n  secret: {reference}\n"
                    expected = sha512(content.encode())
                    for _ in range(routes):
                        expected.update(sha512(b"initial").digest())
                    self.assertEqual(self.write_blueprint(file, reference), expected.hexdigest())

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_content_unchanged(self):
        """Test hash is stable when a referenced `!File` does not change"""
        with NamedTemporaryFile(mode="w+", dir=TMP) as secret:
            self.write_secret(secret, "initial")
            with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
                reference = f"!File {secret.name}"
                self.assertEqual(
                    self.write_blueprint(file, reference),
                    self.write_blueprint(file, reference),
                )

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_unreadable_hash_stable(self):
        """Test hash is stable when a referenced `!File` cannot be read"""
        for label, reference in (
            ("missing file", f"!File {Path(TMP) / generate_id()}"),
            ("path from a tag", f'!File [!Env [{generate_id()}, "{TMP}/fallback"], "default"]'),
            ("path from a mapping", f'!File {{path: "{TMP}/fallback"}}'),
            ("path no syscall can take", '!File "\\0"'),
            ("deeply nested", "[" * 50 + f'!File "{TMP}/fallback"' + "]" * 50),
        ):
            with (
                self.subTest(label),
                NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file,
            ):
                self.assertEqual(
                    self.write_blueprint(file, reference),
                    self.write_blueprint(file, reference),
                )

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_unreadable_discovery_continues(self):
        """Test a blueprint that cannot be hashed does not stop others being discovered"""
        for label, reference in (
            ("path from a mapping", f'!File {{path: "{TMP}/fallback"}}'),
            ("path no syscall can take", '!File "\\0"'),
            ("path outside the filesystem encoding", '!File "\\ud800"'),
            ("sequence containing itself", "&anchor [*anchor]"),
            ("mapping containing itself", "&anchor {key: *anchor}"),
            ("two anchors containing each other", "&outer [{inner: &inner [*outer]}, *inner]"),
        ):
            with (
                self.subTest(label),
                NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as broken,
                NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as healthy,
            ):
                broken.write(f"version: 1\nentries: []\ncontext:\n  secret: {reference}\n")
                broken.flush()
                healthy.write(f"version: 1\nentries: []\nmetadata:\n  name: {generate_id()}\n")
                healthy.flush()
                found = [blueprint.path for blueprint in blueprints_find()]
                self.assertIn(Path(healthy.name).name, found)
                self.assertIn(Path(broken.name).name, found)

    @CONFIG.patch("blueprints_dir", TMP)
    def test_file_tag_applied_on_change(self):
        """Test blueprint is re-applied when the contents of a referenced `!File` change"""
        blueprint_id = generate_id()
        with NamedTemporaryFile(mode="w+", dir=TMP) as secret:
            self.write_secret(secret, "initial")
            with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
                file.write(
                    f"version: 1\nentries: []\n"
                    f"metadata:\n  name: {blueprint_id}\n"
                    f"context:\n  secret: !File {secret.name}\n"
                )
                file.flush()
                blueprints_discovery.send()
                instance = BlueprintInstance.objects.filter(name=blueprint_id).first()
                before = instance.last_applied_hash
                self.assertEqual(instance.status, BlueprintInstanceStatus.SUCCESSFUL)
                self.write_secret(secret, "rotated")
                blueprints_discovery.send()
                instance.refresh_from_db()
                self.assertNotEqual(instance.last_applied_hash, before)
