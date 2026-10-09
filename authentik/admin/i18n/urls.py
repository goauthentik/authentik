"""API URLs"""

from authentik.admin.i18n.api import BrandLocaleCatalogViewSet, LocaleCatalogViewSet

api_urlpatterns = [
    ("admin/locale_catalogs", LocaleCatalogViewSet),
    ("admin/locale_catalog_bindings", BrandLocaleCatalogViewSet),
]
