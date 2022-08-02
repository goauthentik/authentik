"""Test blueprints v1 tasks"""
from tempfile import NamedTemporaryFile, gettempdir, mkdtemp, tempdir

from django.test import TransactionTestCase
from yaml import dump

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.exporter import Exporter
from authentik.blueprints.v1.importer import Importer, transaction_rollback
from authentik.blueprints.v1.tasks import blueprints_discover, blueprints_find
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_login.models import UserLoginStage

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
        blueprints_discover()
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
            blueprints_discover()
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
        blueprints_discover()
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
            blueprints_discover()
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
            blueprints_discover()
            self.assertEqual(
                BlueprintInstance.objects.first().last_applied_hash,
                (
                    "fc62fea96067da8592bdf90927246d0ca150b045447df93b0652a0e20a8bc327"
                    "681510b5db37ea98759c61f9a98dd2381f46a3b5a2da69dfb45158897f14e824"
                ),
            )
            self.assertEqual(BlueprintInstance.objects.first().metadata, {
                "name": "foo",
                "labels": {},
            })
