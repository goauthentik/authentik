"""authentik admin mixins"""
from django.contrib.auth.mixins import UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """Make sure user is administrator"""

    def test_func(self):
        return self.request.user.is_superuser
