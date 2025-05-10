"""Enterprise tasks"""

from dramatiq.actor import actor

from authentik.enterprise.license import LicenseKey


@actor
def enterprise_update_usage():
    """Update enterprise license status"""
    LicenseKey.get_total().record_usage()
