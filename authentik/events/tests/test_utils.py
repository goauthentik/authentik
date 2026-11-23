"""cleanse_dict/cleanse_item tests"""

from django.test import TestCase

from authentik.events.utils import cleanse_dict


class TestCleanseDict(TestCase):
    """Test cleanse_dict/cleanse_item"""

    def test_list_value_not_mutated_in_place(self):
        """cleanse_dict must not mutate list/tuple/set values of the source dict it
        is given -- callers rely on the passed-in dict remaining usable afterwards
        (e.g. flow plan context, which is cleansed purely for tracing/audit purposes)."""
        original_items = ["foo", "bar"]
        # Any key containing "auth" (case-insensitive) matches Django's hidden_settings
        # regex as a substring, which is true of every `goauthentik.io/...` flow
        # plan context key.
        source = {"goauthentik.io/some-key": original_items}

        result = cleanse_dict(source)

        self.assertEqual(original_items, ["foo", "bar"])
        self.assertEqual(result["goauthentik.io/some-key"], ["********************"] * 2)

    def test_set_value_not_mutated_in_place(self):
        """Same as above, for a set value (which doesn't support item assignment at all)."""
        original_items = {"foo"}
        source = {"goauthentik.io/some-key": original_items}

        result = cleanse_dict(source)

        self.assertEqual(original_items, {"foo"})
        self.assertEqual(result["goauthentik.io/some-key"], {"********************"})
