from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from authentik.lib.models import SerializerModel
from django.db import models
from uuid import uuid4
from authentik.core.models import Group, User


# # Names
# Lifecycle
# Access reviews
# Access lifecycle
# Governance
# Audit
# Compliance

# Lifecycle
# Lifecycle review
# Review
# Access review
# Compliance review
# X Scheduled review


# Only some objects supported?
#
# For disabling support:
# Application
# Provider
# Outpost (simply setting the list of providers to empty in the outpost itself)
# Flow
# Users
# Groups <- will get tricky
# Roles
# Sources
# Tokens (api, app_pass)
# Brands
# Outpost integrations
#
# w/o disabling support
# System Settings
# everything else
#   would need to show in an audit dashboard cause not all have pages to get details

# "default" policy for objects, by default, everlasting


class AuditPolicyFailAction(models.TextChoices):
    # For preview
    NOTHING = "nothing"
    # Disable the thing failing, HOW
    DISABLE = "disable"
    # Emit events
    WARN = "warn"


class LifecycleRule(SerializerModel):
    pass


class ReviewRule(SerializerModel):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    # Check every 6 months, allow for daily/weekly/first of month, etc.
    interval = models.TextField()  # timedelta
    # Preventive notification
    reminder_interval = models.TextField()  # timedelta

    # Must be checked by these
    groups = models.ManyToManyField(Group)
    users = models.ManyToManyField(User)

    # How many of the above must approve
    required_approvals = models.IntegerField(default=1)

    # How long to wait before executing fail action
    grace_period = models.TextField()  # timedelta

    # What to do if not reviewed in time
    fail_action = models.CharField(choices=AuditPolicyFailAction)


class AuditPolicyBinding(SerializerModel):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    # Many to many ? Bind users/groups here instead of on the policy ?
    policy = models.ForeignKey(AuditPolicy, on_delete=models.PROTECT)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField(blank=True)  # optional to apply on all objects of specific type
    content_object = GenericForeignKey("content_type", "object_id")

    # valid -> waiting review -> valid
    # valid -> waiting review -> review overdue -> valid
    # valid -> waiting review -> review overdue -> failed -> valid
    # look at django-fsm or django-viewflow
    status = models.TextField()

    class Meta:
        indexes = (
            models.Index(fields=["content_type"]),
            models.Index(fields=["content_type", "object_id"]),
        )


class AuditHistory:
    pass
