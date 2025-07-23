from django.apps import AppConfig


class TelegramConfig(AppConfig):
    name = "authentik.sources.telegram"
    label = "authentik_sources_telegram"
    verbose_name = "authentik Sources.Telegram"
    mountpoint = "source/telegram/"
    default = True
