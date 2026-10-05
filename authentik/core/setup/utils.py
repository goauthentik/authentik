"""Setup state helpers"""

from structlog.stdlib import get_logger

from authentik.core.apps import Setup

LOGGER = get_logger()

SETUP_FLOW_SLUG = "initial-setup"
SETUP_ADMIN_USERNAME = "akadmin"


def setup_flow_runnable() -> bool:
    """Check whether the out-of-box-experience flow can still complete.

    The flow locks itself to superusers once it has run, and its policies refuse to
    plan it once akadmin has a password. Either state means the flow can no longer
    take an instance through setup."""
    from authentik.core.models import User
    from authentik.flows.models import Flow, FlowAuthenticationRequirement

    if Flow.objects.filter(
        slug=SETUP_FLOW_SLUG, authentication=FlowAuthenticationRequirement.REQUIRE_SUPERUSER
    ).exists():
        return False
    akadmin = User.objects.filter(username=SETUP_ADMIN_USERNAME).first()
    return not (akadmin and akadmin.has_usable_password())


def setup_complete() -> bool:
    """Check whether this tenant has been set up.

    Setup state is recorded in the tenant's flags, which live in the public schema,
    while the objects the setup flow mutates live in the tenant schema. Restoring one
    without the other (a partial backup, or a blueprint export applied to a fresh
    database) leaves the flag unset on an instance that is demonstrably already set
    up, which would otherwise strand every visitor on an unusable setup flow. Repair
    the flag instead, matching the heuristic used by the 0058_setup migration."""
    if Setup.get():
        return True
    if setup_flow_runnable():
        return False
    LOGGER.info("Setup flag is unset but setup can no longer run, marking tenant as set up")
    Setup.set(True)
    return True
