"""flow views tests"""
from django.test import TestCase

from authentik.flows.challenge import AutosubmitChallenge, ChallengeTypes


class TestChallenges(TestCase):
    """Test generic challenges"""

    def test_autosubmit_blank(self):
        """Test blank autosubmit"""
        challenge = AutosubmitChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "url": "http://localhost",
                "attrs": {},
            }
        )
        self.assertTrue(challenge.is_valid(raise_exception=True))
        # Test with an empty value
        challenge = AutosubmitChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "url": "http://localhost",
                "attrs": {"foo": ""},
            }
        )
        self.assertTrue(challenge.is_valid(raise_exception=True))
