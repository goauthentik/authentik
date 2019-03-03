"""passbook audit models"""
from datetime import timedelta
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from ipware import get_client_ip

from passbook.lib.models import CreatedUpdatedModel, UUIDModel

LOGGER = getLogger(__name__)

class AuditEntry(UUIDModel):
    """An individual audit log entry"""

    ACTION_LOGIN = 'login'
    ACTION_LOGIN_FAILED = 'login_failed'
    ACTION_LOGOUT = 'logout'
    ACTION_AUTHORIZE_APPLICATION = 'authorize_application'
    ACTION_SUSPICIOUS_REQUEST = 'suspicious_request'
    ACTION_SIGN_UP = 'sign_up'
    ACTION_PASSWORD_RESET = 'password_reset' # noqa
    ACTION_INVITE_CREATED = 'invitation_created'
    ACTION_INVITE_USED = 'invitation_used'
    ACTIONS = (
        (ACTION_LOGIN, ACTION_LOGIN),
        (ACTION_LOGIN_FAILED, ACTION_LOGIN_FAILED),
        (ACTION_LOGOUT, ACTION_LOGOUT),
        (ACTION_AUTHORIZE_APPLICATION, ACTION_AUTHORIZE_APPLICATION),
        (ACTION_SUSPICIOUS_REQUEST, ACTION_SUSPICIOUS_REQUEST),
        (ACTION_SIGN_UP, ACTION_SIGN_UP),
        (ACTION_PASSWORD_RESET, ACTION_PASSWORD_RESET),
        (ACTION_INVITE_CREATED, ACTION_INVITE_CREATED),
        (ACTION_INVITE_USED, ACTION_INVITE_USED),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.TextField(choices=ACTIONS)
    date = models.DateTimeField(auto_now_add=True)
    app = models.TextField()
    context = JSONField(default=dict, blank=True)
    request_ip = models.GenericIPAddressField()
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def create(action, request, **kwargs):
        """Create AuditEntry from arguments"""
        client_ip, _ = get_client_ip(request)
        if not hasattr(request, 'user'):
            user = None
        else:
            user = request.user
        if isinstance(user, AnonymousUser):
            user = kwargs.get('user', None)
        entry = AuditEntry.objects.create(
            action=action,
            user=user,
            # User 255.255.255.255 as fallback if IP cannot be determined
            request_ip=client_ip or '255.255.255.255',
            context=kwargs)
        LOGGER.debug("Logged %s from %s (%s)", action, user, client_ip)
        return entry

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("you may not edit an existing %s" % self._meta.model_name)
        super().save(*args, **kwargs)

    class Meta:

        verbose_name = _('Audit Entry')
        verbose_name_plural = _('Audit Entries')
