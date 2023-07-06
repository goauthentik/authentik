"""authentik managed models tests"""
from django.test import TestCase

from authentik.blueprints.models import BlueprintInstance, BlueprintRetrievalFailed
from authentik.lib.generators import generate_id


class TestModels(TestCase):
    """Test Models"""

    def test_retrieve_file(self):
        """Test retrieve_file"""
        instance = BlueprintInstance.objects.create(name=generate_id(), path="../etc/hosts")
        with self.assertRaises(BlueprintRetrievalFailed):
            instance.retrieve()
