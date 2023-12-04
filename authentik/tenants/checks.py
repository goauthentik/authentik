from django.core.checks import Error, register

from authentik.lib.config import CONFIG


@register()
def check_embedded_outpost_disabled(app_configs, **kwargs):
    if CONFIG.get_bool("tenants.enabled", False) and not CONFIG.get_bool(
        "outposts.disable_embedded_outpost"
    ):
        return [
            Error(
                "Embedded outpost must be disabled when tenants API is enabled.",
                hint="Disable embedded outpost by setting outposts.disable_embedded_outpost to False, or disable the tenants API by setting tenants.enabled to False",
            )
        ]
    return []
