from rest_framework.fields import BooleanField, ChoiceField, DateTimeField

from authentik.core.api.utils import PassiveSerializer
from authentik.tasks.models import TaskStatus


class SyncStatusSerializer(PassiveSerializer):
    """Provider/source sync status"""

    is_running = BooleanField()
    last_successful_sync = DateTimeField(required=False)
    last_sync_status = ChoiceField(required=False, choices=TaskStatus.choices)
