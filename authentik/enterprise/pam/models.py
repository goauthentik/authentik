from random import sample
from typing import Any
from uuid import uuid4

from django.db import models, transaction
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import CreatedUpdatedModel, ExpiringModel, User
from authentik.lib.models import InternallyManagedMixin, SerializerModel
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class RequestStatus(models.TextChoices):

    CREATED = "created"
    APPROVED = "approved"
    DENIED = "denied"
    REVOKED = "revoked"


class GrantRequest(SerializerModel, ExpiringModel, CreatedUpdatedModel):
    """Request of a user to access target(s)"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="grant_requests_created"
    )
    fulfilled_by = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        related_name="grant_requests_fulfilled",
        null=True,
        default=None,
    )
    revoked_by = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        related_name="grant_requests_revoked",
        null=True,
        default=None,
    )

    # Targets access was requested to
    targets = models.ManyToManyField(PolicyBindingModel, through="GrantRequestTarget")
    # Justification data, inputted by the `created_by` user via a flow, used for approve/deny
    requester_data = models.JSONField(default=dict)
    fulfiller_data = models.JSONField(default=dict)

    status = models.TextField(choices=RequestStatus.choices, default=RequestStatus.CREATED)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.pam.api.grant_requests import GrantRequestSerializer

        return GrantRequestSerializer

    def _rule_satisfied(self, rule: PolicyBindingModelRequestRule, approving_users) -> bool:
        """Whether `approving_users` (pks) satisfies a single rule's reviewer requirements.
        An approval from any individually-named `reviewers` satisfies the rule outright;
        otherwise `min_reviewers` distinct approvers are needed from the reviewer groups,
        either in total or from *each* group when `min_reviewers_is_per_group` is set."""
        if rule.reviewers.filter(pk__in=approving_users).exists():
            return True
        if not rule.min_reviewers_is_per_group:
            return (
                rule.reviewer_groups.filter(users__pk__in=approving_users)
                .values_list("users", flat=True)
                .distinct()
                .count()
                >= rule.min_reviewers
            )
        if not rule.reviewer_groups.exists():
            return False
        for group in rule.reviewer_groups.all():
            if group.users.filter(pk__in=approving_users).distinct().count() < rule.min_reviewers:
                return False
        return True

    def is_satisfied(self) -> bool:
        """Whether enough reviewers have approved to fulfill every rule attached to this
        request's targets. A target with no rule attached needs no more than one approval."""
        approving_users = GrantRequestApproval.objects.filter(
            request=self, status=RequestStatus.APPROVED
        ).values_list("reviewer", flat=True)
        rules = PolicyBindingModelRequestRule.objects.filter(pbms__in=self.targets.all()).distinct()
        if not rules.exists():
            return approving_users.exists()
        return all(self._rule_satisfied(rule, approving_users) for rule in rules)

    @transaction.atomic
    def record_approval(self, user: User, status: RequestStatus, data: dict[str, Any]):
        """Record a single reviewer's approval/denial. A denial immediately finalizes the
        request as denied; an approval only finalizes it (and grants access) once
        `is_satisfied` is true across every rule attached to the request's targets."""
        if self.status != RequestStatus.CREATED:
            return
        GrantRequestApproval.objects.update_or_create(
            request=self, reviewer=user, defaults={"status": status, "data": data}
        )
        if status == RequestStatus.DENIED:
            self._finalize(RequestStatus.DENIED, user, data)
            return
        if not self.is_satisfied():
            return
        self._finalize(RequestStatus.APPROVED, user, data)

    def _finalize(self, status: RequestStatus, user: User, data: dict[str, Any]):
        self.fulfilled_by = user
        self.fulfiller_data = data
        self.status = status
        self.save()
        if status != RequestStatus.APPROVED:
            return
        for target in GrantRequestTarget.objects.filter(request=self).all():
            target_binding = PolicyBinding.objects.create(
                user=self.created_by,
                target=target.target,
                expiring=self.expiring,
                expires=self.expires,
                order=1000,
            )
            target.binding = target_binding
            target.save()

    @property
    def is_active(self) -> bool:
        """Whether this request currently grants live access: approved, and neither
        revoked nor naturally expired yet."""
        if self.status != RequestStatus.APPROVED:
            return False
        if self.expiring and self.expires and self.expires < now():
            return False
        return True

    @transaction.atomic
    def revoke(self, user: User):
        """End an active grant immediately, and mark the request revoked. A no-op unless the
        request is currently approved."""
        if self.status != RequestStatus.APPROVED:
            return
        for target in GrantRequestTarget.objects.filter(request=self, binding__isnull=False):
            # Expire the PolicyBindings created (rather than deleting them,
            # since GrantRequestTarget.binding cascades on delete and would
            # take the audit trail with it)
            target.binding.expiring = True
            target.binding.expires = now()
            target.binding.save()
        self.revoked_by = user
        self.status = RequestStatus.REVOKED
        self.save()

    class Meta:
        verbose_name = _("Grant Request")
        verbose_name_plural = _("Grant Requests")

    def __str__(self):
        return f"Grant Request {self.uuid}"


class GrantRequestTarget(InternallyManagedMixin, models.Model):

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    request = models.ForeignKey(GrantRequest, on_delete=models.CASCADE)
    binding = models.ForeignKey(PolicyBinding, on_delete=models.CASCADE, null=True)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Grant Request Target")
        verbose_name_plural = _("Grant Request Targets")

    def __str__(self):
        return f"Grant Request-target {self.request_id} to {self.target_id}"


class GrantRequestApproval(CreatedUpdatedModel):
    """A single reviewer's approval or denial of a GrantRequest. A request needs enough of
    these, per PolicyBindingModelRequestRule attached to its targets, before it is actually
    fulfilled."""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    request = models.ForeignKey(GrantRequest, on_delete=models.CASCADE, related_name="approvals")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.TextField(choices=RequestStatus.choices)
    data = models.JSONField(default=dict)

    class Meta:
        unique_together = ("request", "reviewer")
        verbose_name = _("Grant Request Approval")
        verbose_name_plural = _("Grant Request Approvals")

    def __str__(self):
        return f"Grant Request Approval {self.uuid}"


class RequestNotificationMode(models.TextChoices):
    """Who to notify when a request is created against a rule."""

    ALL = "all", _("Everyone who can approve")
    DIRECT = "direct", _("Only individually-selected reviewers")
    RANDOM_MIN_REVIEWERS = "random_min_reviewers", _(
        "A random subset of size min_reviewers, from everyone who can approve"
    )


class PolicyBindingModelRequestRule(SerializerModel, CreatedUpdatedModel, PolicyBindingModel):

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    pbms = models.ManyToManyField(
        PolicyBindingModel,
        related_name="request_rules",
        through="PolicyBindingModelRequestRuleTarget",
    )

    reviewer_groups = models.ManyToManyField("authentik_core.Group", blank=True)
    min_reviewers = models.PositiveSmallIntegerField(default=1)
    min_reviewers_is_per_group = models.BooleanField(default=False)
    reviewers = models.ManyToManyField("authentik_core.User", blank=True)

    notification_transports = models.ManyToManyField(
        "authentik_events.NotificationTransport", blank=True
    )
    notification_mode = models.TextField(
        choices=RequestNotificationMode.choices, default=RequestNotificationMode.ALL
    )

    def notification_recipients(self) -> models.QuerySet[User]:
        """Users who should be notified when a request against this rule is created,
        per `notification_mode`."""
        individual = self.reviewers.all()
        if self.notification_mode == RequestNotificationMode.DIRECT:
            return individual
        eligible = User.objects.filter(
            models.Q(pk__in=individual) | models.Q(groups__in=self.reviewer_groups.all())
        ).distinct()
        if self.notification_mode == RequestNotificationMode.RANDOM_MIN_REVIEWERS:
            pks = list(eligible.values_list("pk", flat=True))
            chosen = sample(pks, min(self.min_reviewers, len(pks)))
            return User.objects.filter(pk__in=chosen)
        return eligible

    @property
    def serializer(self):
        from authentik.enterprise.pam.api.request_rules import (
            PolicyBindingModelRequestRuleSerializer,
        )

        return PolicyBindingModelRequestRuleSerializer

    class Meta:
        verbose_name = _("Policy Binding Model Request Rule")
        verbose_name_plural = _("Policy Binding Model Request Rules")

    def __str__(self):
        return f"Policy Binding Model Request rule {self.uuid} ({self.name})"


class PolicyBindingModelRequestRuleTarget(models.Model):
    """Through model for PolicyBindingModelRequestRule.pbms"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    rule = models.ForeignKey(
        PolicyBindingModelRequestRule, on_delete=models.CASCADE, related_name="+"
    )
    pbm = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE, related_name="+")

    class Meta:
        unique_together = ("rule", "pbm")
        verbose_name = _("Policy Binding Model Request Rule Target")
        verbose_name_plural = _("Policy Binding Model Request Rule Targets")

    def __str__(self):
        return f"Policy Binding Model Request Rule Target {self.rule_id} to {self.pbm_id}"
