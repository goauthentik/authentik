"""GitLab Type tests"""

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.gitlab import GitLabType

GITLAB_USER = {
    "preferred_username": "dev_gitlab",
    "email": "dev@gitlab.com",
    "name": "Dev",
}


class TestTypeGitLab(TestCase):
    """OAuth Source tests for GitLab"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="gitlab_test",
            slug="gitlab_test",
            provider_type="gitlab",
        )

    def test_enroll_context(self):
        """Test GitLab Enrollment context"""
        ak_context = GitLabType().get_base_user_properties(source=self.source, info=GITLAB_USER)
        self.assertEqual(ak_context["username"], GITLAB_USER["preferred_username"])
        self.assertEqual(ak_context["email"], GITLAB_USER["email"])
        self.assertEqual(ak_context["name"], GITLAB_USER["name"])
