"""Telegram source API views"""
from django.urls import path

from authentik.sources.telegram.api.property_mappings import TelegramSourcePropertyMappingViewSet
from authentik.sources.telegram.api.source import TelegramSourceViewSet
from authentik.sources.telegram.api.source_connection import UserTelegramSourceConnectionViewSet, \
    GroupTelegramSourceConnectionViewSet
from authentik.sources.telegram.views import TelegramLoginView, TelegramStartView

urlpatterns = [
    path("<slug:source_slug>/start/", TelegramStartView.as_view(), name="start"),
    path("<slug:source_slug>/", TelegramLoginView.as_view(), name="login"),
]

api_urlpatterns = [
    ("propertymappings/source/telegram", TelegramSourcePropertyMappingViewSet),
    ("sources/user_connections/telegram", UserTelegramSourceConnectionViewSet),
    ("sources/group_connections/telegram", GroupTelegramSourceConnectionViewSet),
    ("sources/telegram", TelegramSourceViewSet),
]
