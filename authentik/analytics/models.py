"""authentik analytics mixins"""

from typing import Any

from django.utils.translation import gettext_lazy as _


class AnalyticsMixin:
    @classmethod
    def get_analytics_description(cls) -> dict[str, str]:
        object_name = _(cls._meta.verbose_name)
        count_desc = _("Number of {object_name} objects".format_map({"object_name": object_name}))
        return {
            "count": count_desc,
        }

    @classmethod
    def get_analytics_data(cls) -> dict[str, Any]:
        return {"count": cls.objects.all().count()}
