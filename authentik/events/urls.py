"""API URLs"""
from authentik.events.api.events import EventViewSet
from authentik.events.api.notification_mappings import NotificationWebhookMappingViewSet
from authentik.events.api.notification_rules import NotificationRuleViewSet
from authentik.events.api.notification_transports import NotificationTransportViewSet
from authentik.events.api.notifications import NotificationViewSet

api_urlpatterns = [
    ("events/events", EventViewSet),
    ("events/notifications", NotificationViewSet),
    ("events/transports", NotificationTransportViewSet),
    ("events/rules", NotificationRuleViewSet),
    ("propertymappings/notification", NotificationWebhookMappingViewSet),
]
