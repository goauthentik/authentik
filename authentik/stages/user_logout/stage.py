"""Logout stage logic"""
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse

from authentik.flows.stage import StageView


class UserLogoutStageView(StageView):
    """Finalise Authentication flow by logging the user in"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Remove the user from the current session"""
        self.logger.debug(
            "Logged out",
            user=request.user,
            flow_slug=self.executor.flow.slug,
        )
        logout(self.request)
        return self.executor.stage_ok()
