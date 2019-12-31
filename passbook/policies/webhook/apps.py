"""passbook Webhook policy app config"""

from django.apps import AppConfig


class PassbookPoliciesWebhookConfig(AppConfig):
    """passbook Webhook policy app config"""

    name = "passbook.policies.webhook"
    label = "passbook_policies_webhook"
    verbose_name = "passbook Policies.Webhook"
