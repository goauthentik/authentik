"""Test API Utils"""

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    HyperlinkedModelSerializer,
)
from rest_framework.serializers import (
    ModelSerializer as BaseModelSerializer,
)
from rest_framework.test import APITestCase

from authentik.core.api.utils import (
    INT_64_MAX,
    INT_64_MIN,
    JSONDictField,
    is_dict,
    normalize_large_integers,
)
from authentik.core.api.utils import ModelSerializer as CustomModelSerializer
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

    def test_normalize_large_integers(self):
        """Test that integers outside int64 are normalized to strings."""
        lower = INT_64_MIN - 1
        upper = INT_64_MAX + 1
        result = normalize_large_integers(
            {
                "lower": lower,
                "upper": upper,
                "valid_low": INT_64_MIN,
                "valid_high": INT_64_MAX,
                "nested": {"numbers": [lower, 0, upper]},
                "bool": True,
            }
        )

        self.assertEqual(result["lower"], str(lower))
        self.assertEqual(result["upper"], str(upper))
        self.assertEqual(result["valid_low"], INT_64_MIN)
        self.assertEqual(result["valid_high"], INT_64_MAX)
        self.assertEqual(result["nested"]["numbers"], [str(lower), 0, str(upper)])
        self.assertIs(result["bool"], True)

    def test_json_dict_field_normalizes_large_integers(self):
        """Test JSONDictField normalization for input and output values."""
        field = JSONDictField()
        value = INT_64_MAX + 1
        validated = field.run_validation({"id": value})

        self.assertEqual(validated["id"], str(value))
        self.assertEqual(field.to_representation({"id": value})["id"], str(value))
