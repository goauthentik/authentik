"""Test blueprints v1 tasks"""

from hashlib import sha512
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
            apply_blueprint(instance.pk)
            instance.refresh_from_db()
            self.assertEqual(instance.last_applied_hash, "")
            self.assertEqual(
                instance.status,
                BlueprintInstanceStatus.UNKNOWN,
            )
