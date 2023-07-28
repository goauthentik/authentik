"""Test Users Avatars"""

from django.test import TestCase

from authentik.core.models import User


class TestUserKrb5(TestCase):
    """Test Users avatars"""

    def setUp(self) -> None:
        self.user = User.objects.create(username="test-user")

    def test_set_password_increment_kvno(self):
        """Test avatars none"""
        self.user.set_password("test1")
        kvno = self.user.krb5_kvno
        self.user.set_password("test2")
        self.assertLess(kvno, self.user.krb5_kvno)

    def test_kvno_wrapping_maxvalue(self):
        """Test avatars none"""
        self.user.krb5_kvno = 2**32 - 1
        self.user.set_password("test3")
        self.assertEqual(self.user.krb5_kvno, 1)

    def test_kvno_skip_mod256(self):
        """Test avatars none"""
        self.user.krb5_kvno = 2**8 - 1
        self.user.set_password("test4")
        self.assertEqual(self.user.krb5_kvno, 2**8 + 1)
