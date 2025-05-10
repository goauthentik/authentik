"""authentik tenants system checks"""

from django.core.checks import Error, register

from authentik.common.config import CONFIG


@register()
def check_embedded_outpost_disabled(app_configs, **kwargs):
    """Check that when the tenants API is enabled, the embedded outpost is disabled"""
    if CONFIG.get_bool("tenants.enabled", False) and not CONFIG.get_bool(
        "outposts.disable_embedded_outpost"
    ):
        return [
            Error(
                "Embedded outpost must be disabled when tenants API is enabled.",
                hint="Disable embedded outpost by setting outposts.disable_embedded_outpost to "
                "True, or disable the tenants API by setting tenants.enabled to False",
            )
        ]
    return []
