"""Telegram source"""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any

from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.http import HttpRequest
from rest_framework import serializers
from rest_framework.fields import CharField, BooleanField
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import Source, PropertyMapping, UserSourceConnection, GroupSourceConnection
from authentik.core.types import UILoginButton
from authentik.flows.challenge import Challenge, ChallengeResponse, RedirectChallenge
from authentik.stages.identification.stage import LoginChallengeMixin


class TelegramLoginChallenge(LoginChallengeMixin, Challenge):
    component = CharField(default="ak-source-telegram")
    bot_username = CharField(help_text=_("Telegram bot username"))
    request_access = BooleanField()


class TelegramChallengeResponse(ChallengeResponse):
    component = CharField(default="ak-source-telegram")

    id = serializers.IntegerField()
    first_name = serializers.CharField(max_length=255, required=False)
    last_name = serializers.CharField(max_length=255, required=False)
    username = serializers.CharField(max_length=255, required=False)
    photo_url = serializers.URLField(required=False)
    auth_date = serializers.IntegerField(required=True)
    hash = serializers.CharField(max_length=64, required=True)

    def validate_auth_date(self, auth_date):
        if datetime.fromtimestamp(auth_date) < datetime.now() - timedelta(minutes=5):
            raise serializers.ValidationError(_("Authentication date is too old"))
        return auth_date

    def validate(self, attrs):
        attrs_to_check = attrs.copy()
        attrs_to_check.pop("component")
        attrs_to_check.pop("hash")
        check_str = '\n'.join([f'{key}={value}' for key, value in sorted(attrs_to_check.items())])
        digest = hmac.new(hashlib.sha256(self.stage.source.bot_token.encode('utf-8')).digest(),
                          check_str.encode('utf-8'),
                          'sha256').hexdigest()
        if not hmac.compare_digest(digest, attrs['hash']):
            raise serializers.ValidationError(_('Invalid hash'))
        return attrs


class TelegramSourcePropertyMapping(PropertyMapping):
    """Map Telegram properties to User or Group object attributes"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-telegram-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.telegram.api.property_mappings import TelegramSourcePropertyMappingSerializer

        return TelegramSourcePropertyMappingSerializer

    class Meta:
        verbose_name = _("Telegram Source Property Mapping")
        verbose_name_plural = _("Telegram Source Property Mappings")


class TelegramSource(Source):
    """Log in with Telegram."""

    bot_username = models.CharField(max_length=255, help_text=_("Telegram bot username"))
    bot_token = models.CharField(max_length=255, help_text=_("Telegram bot token"))
    request_access = models.BooleanField(default=False,
                                         help_text=_("Request access to send messages from your bot."))

    @property
    def component(self) -> str:
        return 'ak-source-telegram-form'

    @property
    def icon_url(self) -> str | None:
        icon = super().icon_url
        if not icon:
            icon = static("authentik/sources/telegram.svg")
        return icon

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.sources.telegram.api.source import TelegramSourceSerializer
        return TelegramSourceSerializer

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        return UILoginButton(
            challenge=RedirectChallenge(
                data={
                    "to": reverse(
                        "authentik_sources_telegram:start",
                        kwargs={"source_slug": self.slug},
                    ),
                }
            ),
            name=self.name,
            icon_url=self.icon_url,
        )

    @property
    def property_mapping_type(self) -> "type[PropertyMapping]":
        return TelegramSourcePropertyMapping

    def get_base_user_properties(self, info: dict[str, Any]={}, **kwargs) -> dict[str, Any | dict[str, Any]]:
        name = info.get('first_name', '')
        if 'last_name' in info:
            name += ' ' + info['last_name']
        return {'username': info.get('username', None), 'email': None,
                'name': name if name else None}

    def get_base_group_properties(self, group_id: str, **kwargs):
        return {
            "name": group_id,
        }

    class Meta:
        verbose_name = _("Telegram Source")
        verbose_name_plural = _("Telegram Sources")


class UserTelegramSourceConnection(UserSourceConnection):
    """Connect user and Telegram source"""

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.telegram.api.source_connection import UserTelegramSourceConnectionSerializer

        return UserTelegramSourceConnectionSerializer

    class Meta:
        verbose_name = _("User Telegram Source Connection")
        verbose_name_plural = _("User Telegram Source Connections")


class GroupTelegramSourceConnection(GroupSourceConnection):
    """Group-source connection for Telegram"""

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.telegram.api.source_connection import GroupTelegramSourceConnectionSerializer

        return GroupTelegramSourceConnectionSerializer

    class Meta:
        verbose_name = _("Group Telegram Source Connection")
        verbose_name_plural = _("Group Telegram Source Connections")
