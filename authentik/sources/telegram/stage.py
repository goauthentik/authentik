import hashlib
import hmac
from datetime import datetime, timedelta

from django.utils.translation import gettext_lazy as _
from rest_framework.fields import BooleanField, CharField, IntegerField, URLField
from rest_framework.serializers import ValidationError

from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.stages.identification.stage import LoginChallengeMixin


class TelegramLoginChallenge(LoginChallengeMixin, Challenge):
    component = CharField(default="ak-source-telegram")
    bot_username = CharField(help_text=_("Telegram bot username"))
    request_message_access = BooleanField()


class TelegramChallengeResponse(ChallengeResponse):
    component = CharField(default="ak-source-telegram")

    id = IntegerField()
    first_name = CharField(max_length=255, required=False)
    last_name = CharField(max_length=255, required=False)
    username = CharField(max_length=255, required=False)
    photo_url = URLField(required=False)
    auth_date = IntegerField(required=True)
    hash = CharField(max_length=64, required=True)

    def validate_auth_date(self, auth_date):
        if datetime.fromtimestamp(auth_date) < datetime.now() - timedelta(minutes=5):
            raise ValidationError(_("Authentication date is too old"))
        return auth_date

    def validate(self, attrs):
        # Check the response as defined in https://core.telegram.org/widgets/login
        attrs_to_check = attrs.copy()
        attrs_to_check.pop("component")
        attrs_to_check.pop("hash")
        check_str = "\n".join([f"{key}={value}" for key, value in sorted(attrs_to_check.items())])
        digest = hmac.new(
            hashlib.sha256(self.stage.source.bot_token.encode("utf-8")).digest(),
            check_str.encode("utf-8"),
            "sha256",
        ).hexdigest()
        if not hmac.compare_digest(digest, attrs["hash"]):
            raise ValidationError(_("Invalid hash"))
        return attrs
