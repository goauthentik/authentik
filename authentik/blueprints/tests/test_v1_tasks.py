"""Test blueprints v1 tasks"""
from tempfile import NamedTemporaryFile, mkdtemp

from django.test import TransactionTestCase
from yaml import dump

from authentik.blueprints.models import BlueprintInstance, BlueprintInstanceStatus
from authentik.blueprints.v1.tasks import apply_blueprint, blueprints_discover, blueprints_find
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
            blueprints_discover()  # pylint: disable=no-value-for-parameter
            self.assertEqual(
                BlueprintInstance.objects.first().last_applied_hash,
                (
                    "e52bb445b03cd36057258dc9f0ce0fbed8278498ee1470e45315293e5f026d1b"
                    "d1f9b3526871c0003f5c07be5c3316d9d4a08444bd8fed1b3f03294e51e44522"
                ),
            )
            self.assertEqual(BlueprintInstance.objects.first().metadata, {})

    @CONFIG.patch("blueprints_dir", TMP)
    def test_valid_updated(self):
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
            blueprints_discover()  # pylint: disable=no-value-for-parameter
            self.assertEqual(
                BlueprintInstance.objects.first().last_applied_hash,
                (
                    "e52bb445b03cd36057258dc9f0ce0fbed8278498ee1470e45315293e5f026d1b"
                    "d1f9b3526871c0003f5c07be5c3316d9d4a08444bd8fed1b3f03294e51e44522"
                ),
            )
            self.assertEqual(BlueprintInstance.objects.first().metadata, {})
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
            blueprints_discover()  # pylint: disable=no-value-for-parameter
            self.assertEqual(
                BlueprintInstance.objects.first().last_applied_hash,
                (
                    "fc62fea96067da8592bdf90927246d0ca150b045447df93b0652a0e20a8bc327"
                    "681510b5db37ea98759c61f9a98dd2381f46a3b5a2da69dfb45158897f14e824"
                ),
            )
            self.assertEqual(
                BlueprintInstance.objects.first().metadata,
                {
                    "name": "foo",
                    "labels": {},
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
            apply_blueprint(instance.pk)  # pylint: disable=no-value-for-parameter
            instance.refresh_from_db()
            self.assertEqual(instance.last_applied_hash, "")
            self.assertEqual(
                instance.status,
                BlueprintInstanceStatus.UNKNOWN,
            )
