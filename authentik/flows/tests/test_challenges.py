"""flow views tests"""

from django.test import TestCase

from authentik.flows.challenge import AutosubmitChallenge


class TestChallenges(TestCase):
    """Test generic challenges"""

    def test_autosubmit_blank(self):
        """Test blank autosubmit"""
        challenge = AutosubmitChallenge(
            data={
                "url": "http://localhost",
                "attrs": {},
            }
        )
        self.assertTrue(challenge.is_valid(raise_exception=True))
        # Test with an empty value
        challenge = AutosubmitChallenge(
            data={
                "url": "http://localhost",
                "attrs": {"foo": ""},
            }
        )
        self.assertTrue(challenge.is_valid(raise_exception=True))
