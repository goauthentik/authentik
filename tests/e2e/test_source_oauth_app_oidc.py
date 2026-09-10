"""test OAuth Source login into an OAuth2/OIDC application"""

from time import sleep

from authentik.core.models import SourceUserMatchingModes
from authentik.core.tests.utils import create_test_user
from tests.e2e.oauth_source import (
    DEEP_LINK_URL,
    DEX_EMAIL,
    TestOAuthSource,
    TestOIDCApp,
    source_app_test,
)
from tests.selenium import SeleniumTestCase


class TestSourceOAuthAppOIDC(SeleniumTestCase):
    """test OAuth Source login into an OAuth2/OIDC application"""

    def setUp(self):
        super().setUp()
        self.source = TestOAuthSource(self)
        self.app = TestOIDCApp(self)
        self.source.start()

    @source_app_test
    def test_source_auth(self):
        """test app login via OAuth source (existing user, linked by email)"""
        user = create_test_user(email=DEX_EMAIL)
        self.source.create(user_matching_mode=SourceUserMatchingModes.EMAIL_LINK)
        self.app.start()

        self.app.open()
        self.source.auth()

        self.app.assert_login(user)

    @source_app_test
    def test_source_enroll(self):
        """test app login via OAuth source (new user, enrolled)"""
        self.source.create()
        self.app.start()

        self.app.open()
        user = self.source.enroll()

        self.app.assert_login(user)

    @source_app_test
    def test_source_enroll_auth(self):
        """test app login via OAuth source (enroll, then authenticate again)"""
        self.source.create()
        self.app.start()

        self.app.open()
        user = self.source.enroll()
        self.app.assert_login(user)

        # Log out and log back in, this time without enrolling
        self.driver.get(self.url("authentik_flows:default-invalidation"))
        sleep(1)
        self.app.reopen()
        self.source.auth()

        self.app.assert_login(user)

    @source_app_test
    def test_source_auth_deep_link(self):
        """test app login via OAuth source, started at a deep link into the app"""
        user = create_test_user(email=DEX_EMAIL)
        self.source.create(user_matching_mode=SourceUserMatchingModes.EMAIL_LINK)
        self.app.start()

        self.app.open(DEEP_LINK_URL)
        self.source.auth()

        self.app.assert_login(user, entry=DEEP_LINK_URL)

    @source_app_test
    def test_source_enroll_deep_link(self):
        """test app enrollment via OAuth source, started at a deep link into the app"""
        self.source.create()
        self.app.start()

        self.app.open(DEEP_LINK_URL)
        user = self.source.enroll()

        self.app.assert_login(user, entry=DEEP_LINK_URL)
