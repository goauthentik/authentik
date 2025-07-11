"""Sessions bound to ASN/Network and GeoIP/Continent/etc"""

from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.signals import user_logged_out
from django.contrib.auth.views import redirect_to_login
from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR
from authentik.lib.sentry import SentryIgnoredException
from authentik.root.middleware import ClientIPMiddleware, SessionMiddleware
from authentik.stages.user_login.models import GeoIPBinding, NetworkBinding

SESSION_KEY_BINDING_NET = "authentik/stages/user_login/binding/net"
SESSION_KEY_BINDING_GEO = "authentik/stages/user_login/binding/geo"
LOGGER = get_logger()


class SessionBindingBroken(SentryIgnoredException):
    """Session binding was broken due to specified `reason`"""

    def __init__(  # noqa: PLR0913
        self, reason: str, old_value: str, new_value: str, old_ip: str, new_ip: str
    ) -> None:
        self.reason = reason
        self.old_value = old_value
        self.new_value = new_value
        self.old_ip = old_ip
        self.new_ip = new_ip

    def __repr__(self) -> str:
        return (
            f"Session binding broken due to {self.reason}; "
            f"old value: {self.old_value}, new value: {self.new_value}"
        )

    def to_event(self) -> dict:
        """Convert to dict for usage with event"""
        return {
            "logout_reason": "Session binding broken",
            "binding": {
                "reason": self.reason,
                "previous_value": self.old_value,
                "new_value": self.new_value,
            },
            "ip": {
                "previous": self.old_ip,
                "new": self.new_ip,
            },
        }


def logout_extra(request: HttpRequest, exc: SessionBindingBroken):
    """Similar to django's logout method, but able to carry more info to the signal"""
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", True):
        user = None
    user_logged_out.send(
        sender=user.__class__, request=request, user=user, event_extra=exc.to_event()
    )
    request.session.flush()
    if hasattr(request, "user"):
        from django.contrib.auth.models import AnonymousUser

        request.user = AnonymousUser()


class BoundSessionMiddleware(SessionMiddleware):
    """Sessions bound to ASN/Network and GeoIP/Continent/etc"""

    def process_request(self, request: HttpRequest):
        super().process_request(request)
        try:
            self.recheck_session(request)
        except SessionBindingBroken as exc:
            LOGGER.warning("Session binding broken", exc=exc)
            # At this point, we need to logout the current user
            # however since this middleware has to run before the `AuthenticationMiddleware`
            # we don't have access to the user yet
            # Logout will still work, however event logs won't display the user being logged out
            AuthenticationMiddleware(lambda request: request).process_request(request)
            logout_extra(request, exc)
            request.session.clear()
            return redirect_to_login(request.get_full_path())
        return None

    def recheck_session(self, request: HttpRequest):
        """Check if a session is still valid with a changed IP"""
        last_ip = request.session.get(request.session.model.Keys.LAST_IP)
        new_ip = ClientIPMiddleware.get_client_ip(request)
        # Check changed IP
        if new_ip == last_ip:
            return
        configured_binding_net = request.session.get(
            SESSION_KEY_BINDING_NET, NetworkBinding.NO_BINDING
        )
        configured_binding_geo = request.session.get(
            SESSION_KEY_BINDING_GEO, GeoIPBinding.NO_BINDING
        )
        if configured_binding_net != NetworkBinding.NO_BINDING:
            self.recheck_session_net(configured_binding_net, last_ip, new_ip)
        if configured_binding_geo != GeoIPBinding.NO_BINDING:
            self.recheck_session_geo(configured_binding_geo, last_ip, new_ip)
        # If we got to this point without any error being raised, we need to
        # update the last saved IP to the current one
        if SESSION_KEY_BINDING_NET in request.session or SESSION_KEY_BINDING_GEO in request.session:
            # Only set the last IP in the session if there's a binding specified
            # (== basically requires the user to be logged in)
            request.session[request.session.model.Keys.LAST_IP] = new_ip

    def recheck_session_net(self, binding: NetworkBinding, last_ip: str, new_ip: str):
        """Check network/ASN binding"""
        last_asn = ASN_CONTEXT_PROCESSOR.asn(last_ip)
        new_asn = ASN_CONTEXT_PROCESSOR.asn(new_ip)
        if not last_asn or not new_asn:
            raise SessionBindingBroken(
                "network.missing",
                ASN_CONTEXT_PROCESSOR.asn_to_dict(last_asn),
                ASN_CONTEXT_PROCESSOR.asn_to_dict(new_asn),
                last_ip,
                new_ip,
            )
        if binding in [
            NetworkBinding.BIND_ASN,
            NetworkBinding.BIND_ASN_NETWORK,
            NetworkBinding.BIND_ASN_NETWORK_IP,
        ]:
            # Check ASN which is required for all 3 modes
            if last_asn.autonomous_system_number != new_asn.autonomous_system_number:
                raise SessionBindingBroken(
                    "network.asn",
                    last_asn.autonomous_system_number,
                    new_asn.autonomous_system_number,
                    last_ip,
                    new_ip,
                )
        if binding in [NetworkBinding.BIND_ASN_NETWORK, NetworkBinding.BIND_ASN_NETWORK_IP]:
            # Check Network afterwards
            if last_asn.network != new_asn.network:
                raise SessionBindingBroken(
                    "network.asn_network",
                    str(last_asn.network),
                    str(new_asn.network),
                    last_ip,
                    new_ip,
                )
        if binding in [NetworkBinding.BIND_ASN_NETWORK_IP]:
            # Only require strict IP checking
            if last_ip != new_ip:
                raise SessionBindingBroken(
                    "network.ip",
                    last_ip,
                    new_ip,
                    last_ip,
                    new_ip,
                )

    def recheck_session_geo(self, binding: GeoIPBinding, last_ip: str, new_ip: str):
        """Check GeoIP binding"""
        last_geo = GEOIP_CONTEXT_PROCESSOR.city(last_ip)
        new_geo = GEOIP_CONTEXT_PROCESSOR.city(new_ip)
        if not last_geo or not new_geo:
            raise SessionBindingBroken(
                "geoip.missing",
                GEOIP_CONTEXT_PROCESSOR.city_to_dict(last_geo),
                GEOIP_CONTEXT_PROCESSOR.city_to_dict(new_geo),
                last_ip,
                new_ip,
            )
        if binding in [
            GeoIPBinding.BIND_CONTINENT,
            GeoIPBinding.BIND_CONTINENT_COUNTRY,
            GeoIPBinding.BIND_CONTINENT_COUNTRY_CITY,
        ]:
            # Check Continent which is required for all 3 modes
            if last_geo.continent != new_geo.continent:
                raise SessionBindingBroken(
                    "geoip.continent",
                    last_geo.continent,
                    new_geo.continent,
                    last_ip,
                    new_ip,
                )
        if binding in [
            GeoIPBinding.BIND_CONTINENT_COUNTRY,
            GeoIPBinding.BIND_CONTINENT_COUNTRY_CITY,
        ]:
            # Check Country afterwards
            if last_geo.country != new_geo.country:
                raise SessionBindingBroken(
                    "geoip.country",
                    last_geo.country,
                    new_geo.country,
                    last_ip,
                    new_ip,
                )
        if binding in [GeoIPBinding.BIND_CONTINENT_COUNTRY_CITY]:
            # Check city afterwards
            if last_geo.city != new_geo.city:
                raise SessionBindingBroken(
                    "geoip.city",
                    last_geo.city,
                    new_geo.city,
                    last_ip,
                    new_ip,
                )
