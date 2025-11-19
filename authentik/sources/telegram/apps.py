from authentik.blueprints.apps import ManagedAppConfig


class TelegramConfig(ManagedAppConfig):
    name = "authentik.sources.telegram"
    label = "authentik_sources_telegram"
    verbose_name = "authentik Sources.Telegram"
    mountpoint = "source/telegram/"
    default = True
