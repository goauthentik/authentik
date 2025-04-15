"""Test API Utils"""

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    HyperlinkedModelSerializer,
)
from rest_framework.serializers import (
    ModelSerializer as BaseModelSerializer,
)
from rest_framework.test import APITestCase

from authentik.core.api.utils import ModelSerializer as CustomModelSerializer
from authentik.core.api.utils import is_dict
from authentik.lib.utils.reflection import all_subclasses


class TestAPIUtils(APITestCase):
    """Test API Utils"""

    def test_is_dict(self):
        """Test is_dict"""
        self.assertIsNone(is_dict({}))
        with self.assertRaises(ValidationError):
            is_dict("foo")

    def test_all_serializers_descend_from_custom(self):
        """Test that every serializer we define descends from our own ModelSerializer"""
        # Weirdly, there's only one serializer in `rest_framework` which descends from
        # ModelSerializer: HyperlinkedModelSerializer
        expected = {CustomModelSerializer, HyperlinkedModelSerializer}
        actual = set(all_subclasses(BaseModelSerializer)) - set(
            all_subclasses(CustomModelSerializer)
        )

        self.assertEqual(expected, actual)
