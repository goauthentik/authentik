from typing import Any
from uuid import uuid4

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import CreatedUpdatedModel, ExpiringModel, User
from authentik.lib.models import InternallyManagedMixin, SerializerModel
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class PersonaTemplate(SerializerModel, CreatedUpdatedModel, PolicyBindingModel):
    """Admin-defined template a user can self-instantiate a Persona from (via a GrantRequest,
    same as requesting access to an Application). Because this is itself a PolicyBindingModel,
    an admin can attach a PolicyBindingModelRequestRule to it to control who may approve an
    instantiation request, exactly like they would for an Application.

    Owns the actor allowlist so admins have one place to change which agents are trusted,
    rather than editing every Persona instantiated from this template individually."""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()

    # Actors (agents) allowed to present an `actor_token` and obtain a token exchanged for
    # a persona instantiated from this template. Mirrors the shape of
    # OAuth2Provider.jwt_federation_providers/_sources: the actor's own token is verified
    # through that same trust, then checked against these allowlists.
    actor_providers = models.ManyToManyField(
        "authentik_providers_oauth2.OAuth2Provider", blank=True, related_name="+"
    )
    actor_sources = models.ManyToManyField(
        "authentik_sources_oauth.OAuthSource", blank=True, related_name="+"
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.pam.api.persona_templates import PersonaTemplateSerializer

        return PersonaTemplateSerializer

    class Meta:
        verbose_name = _("Persona Template")
        verbose_name_plural = _("Persona Templates")

    def __str__(self):
        return f"Persona Template {self.name}"


class Persona(ExpiringModel, User):
    # Inherited:
    #  - parent.email
    #  - parent.name (customisable)
    # Modified:
    #  - parent.username
    #  - parent.groups

    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personas")
    # Set when this persona was self- or admin-instantiated from a PersonaTemplate, whose
    # actor_providers/actor_sources then govern delegation for this persona. Personas created
    # directly (no template) cannot be delegated to via actor_token.
    template = models.ForeignKey(
        PersonaTemplate,
        on_delete=models.SET_NULL,
        related_name="personas",
        null=True,
        blank=True,
        default=None,
    )

    @staticmethod
    def create_for_user(name: str, user: User, template: PersonaTemplate | None = None) -> Persona:
        return Persona.objects.create(username=name, name=user.name, parent=user, template=template)

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Persona")
        verbose_name_plural = _("Personas")

    def __str__(self):
        return f"Persona {self.username} for {self.parent_id}"


class Grant(ExpiringModel, CreatedUpdatedModel):
    """Grant for a persona to access `target`, given after manual/automatic approval."""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE)

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Grant")
        verbose_name_plural = _("Grants")

    def __str__(self):
        return f"Grant {self.uuid}"


class RequestStatus(models.TextChoices):

    CREATED = "created"
    APPROVED = "approved"
    DENIED = "denied"


class GrantRequest(SerializerModel, ExpiringModel, CreatedUpdatedModel):
    """Request of a user to access target(s) via Persona"""

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
    # Persona the requesting user wants the access granted to, instead of themselves.
    # Must belong to `created_by`.
    persona = models.ForeignKey(
        "Persona",
        on_delete=models.SET_NULL,
        related_name="grant_requests",
        null=True,
        blank=True,
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

    @transaction.atomic
    def fulfill(self, status: RequestStatus, user: User, data: dict[str, Any]):
        if self.status != RequestStatus.CREATED:
            return
        self.fulfilled_by = user
        self.fulfiller_data = data
        self.status = status
        self.save()
        if self.status != RequestStatus.APPROVED:
            return
        grant_user = self.persona or self.created_by
        for target in GrantRequestTarget.objects.filter(request=self).all():
            template = PersonaTemplate.objects.filter(pbm_uuid=target.target_id).first()
            if template:
                # Requesting a PersonaTemplate instantiates a Persona rather than granting
                # access to an existing one; skip if the user already has one from it.
                if not Persona.objects.filter(template=template, parent=self.created_by).exists():
                    Persona.create_for_user(
                        f"{template.name}-{self.created_by.username}",
                        self.created_by,
                        template=template,
                    )
                continue
            target_binding = PolicyBinding.objects.create(
                user=grant_user,
                target=target.target,
                expiring=self.expiring,
                expires=self.expires,
                order=1000,
            )
            target.binding = target_binding
            target.save()
            if self.persona:
                Grant.objects.create(
                    persona=self.persona,
                    target=target.target,
                    expiring=self.expiring,
                    expires=self.expires,
                )

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


class PolicyBindingModelRequestRule(SerializerModel, CreatedUpdatedModel, PolicyBindingModel):

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    pbm = models.ForeignKey(
        PolicyBindingModel, on_delete=models.CASCADE, related_name="request_rules"
    )

    reviewer_groups = models.ManyToManyField("authentik_core.Group", blank=True)
    min_reviewers = models.PositiveSmallIntegerField(default=1)
    min_reviewers_is_per_group = models.BooleanField(default=False)
    reviewers = models.ManyToManyField("authentik_core.User", blank=True)

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
        return f"Policy Binding Model Request rule {self.uuid} to {self.pbm_id}"
