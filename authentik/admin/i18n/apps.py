from authentik.blueprints.apps import ManagedAppConfig


class AuthentikI18nConfig(ManagedAppConfig):
    name = "authentik.admin.i18n"
    label = "authentik_admin_i18n"
    verbose_name = "authentik Internationalization"
    default = True

    def ready(self) -> None:
        from authentik.admin.i18n.translation import install_catalog_translation

        install_catalog_translation()
        return super().ready()
