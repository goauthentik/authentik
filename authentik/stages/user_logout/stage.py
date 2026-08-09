"""Logout stage logic"""

from django.contrib.auth import logout
from django.dispatch import Signal
from django.http import HttpRequest, HttpResponse
from structlog.stdlib import get_logger

from authentik.flows.stage import StageView

LOGGER = get_logger()

# Custom signal for handling
# front-channel logouts
flow_pre_user_logout = Signal()


class UserLogoutStageView(StageView):
    """Logout stage that logs out the user"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Log out user and send pre-logout signal"""

        # This signal is for handling SAML front-channel logouts
        flow_pre_user_logout.send(
            sender=self.__class__, request=request, user=request.user, executor=self.executor
        )

        LOGGER.debug(
            "Logged out",
            user=request.user,
            flow_slug=self.executor.flow.slug,
        )
        logout(self.request)

        return self.executor.stage_ok()
