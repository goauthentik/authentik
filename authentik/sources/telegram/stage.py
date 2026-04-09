from django.utils.translation import gettext_lazy as _
from rest_framework.fields import BooleanField, CharField

from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.sources.telegram.telegram import TelegramAuth
from authentik.stages.identification.stage import LoginChallengeMixin


class TelegramLoginChallenge(LoginChallengeMixin, Challenge):
    component = CharField(default="ak-source-telegram")
    bot_username = CharField(help_text=_("Telegram bot username"))
    request_message_access = BooleanField()


class TelegramChallengeResponse(TelegramAuth, ChallengeResponse):
    component = CharField(default="ak-source-telegram")

    def get_bot_token(self) -> str:
        return self.stage.source.bot_token

    def validate(self, attrs: dict) -> dict:
        attrs_to_check = attrs.copy()
        component = attrs_to_check.pop("component")
        validated = super().validate(attrs_to_check)
        validated["component"] = component
        return validated
