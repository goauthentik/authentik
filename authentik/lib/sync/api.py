from rest_framework.fields import BooleanField, ChoiceField, DateTimeField

from authentik.core.api.utils import PassiveSerializer
from authentik.tasks.models import TaskStatus


class SyncStatusSerializer(PassiveSerializer):
    """Provider/source sync status"""

    is_running = BooleanField(read_only=True, default=False)
    last_successful_sync = DateTimeField(read_only=True, required=False, default=None)
    last_sync_status = ChoiceField(
        read_only=True,
        required=False,
        default=None,
        choices=TaskStatus.choices,
    )
