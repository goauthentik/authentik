"""Cloud-gateway client helpers"""
from functools import lru_cache

from authentik_cloud_gateway_client.authenticationPush_pb2_grpc import AuthenticationPushStub
from django.conf import settings
from grpc import (
    UnaryStreamClientInterceptor,
    UnaryUnaryClientInterceptor,
    insecure_channel,
    intercept_channel,
    secure_channel,
    ssl_channel_credentials,
)
from grpc._interceptor import _ClientCallDetails


class AuthInterceptor(UnaryUnaryClientInterceptor, UnaryStreamClientInterceptor):
    """GRPC auth interceptor"""

    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token

    def _intercept_client_call_details(self, details: _ClientCallDetails) -> _ClientCallDetails:
        """inject auth header"""
        metadata = []
        if details.metadata is not None:
            metadata = list(details.metadata)
        metadata.append(
            (
                "authorization",
                f"Bearer {self.token}",
            )
        )
        return _ClientCallDetails(
            details.method,
            details.timeout,
            metadata,
            details.credentials,
            details.wait_for_ready,
            details.compression,
        )

    def intercept_unary_unary(self, continuation, client_call_details: _ClientCallDetails, request):
        return continuation(self._intercept_client_call_details(client_call_details), request)

    def intercept_unary_stream(
        self, continuation, client_call_details: _ClientCallDetails, request
    ):
        return continuation(self._intercept_client_call_details(client_call_details), request)


@lru_cache()
def get_enterprise_token() -> str:
    """Get enterprise license key, if a license is installed, otherwise use the install ID"""
    from authentik.root.install_id import get_install_id

    try:
        from authentik.enterprise.models import License

        valid_license = License.non_expired().order_by("-expiry").first()
        if not valid_license:
            return get_install_id()
        return valid_license.key
    except ImportError:
        return get_install_id()


@lru_cache()
def get_client(addr: str):
    """get a cached client to a cloud-gateway"""
    channel = secure_channel(addr, ssl_channel_credentials)
    if settings.DEBUG:
        channel = insecure_channel(addr)
    channel = intercept_channel(addr, AuthInterceptor(get_enterprise_token()))
    client = AuthenticationPushStub(channel)
    return client
