"""API URLs"""

from authentik.admin.i18n.api import LocaleCatalogViewSet

api_urlpatterns = [
    ("admin/locale_catalogs", LocaleCatalogViewSet),
]
