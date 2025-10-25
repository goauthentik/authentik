from django.http import HttpRequest
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import Application
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.enterprise.providers.ssf.views.auth import SSFTokenAuth


class SSFView(APIView):
    application: Application
    provider: SSFProvider
    logger: BoundLogger

    permission_classes = [IsAuthenticated]

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        self.logger = get_logger().bind()
        super().setup(request, *args, **kwargs)

    def get_authenticators(self):
        return [SSFTokenAuth(self)]
