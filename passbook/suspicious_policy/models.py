"""passbook suspicious request policy"""
from django.db import models
from django.utils.translation import gettext as _
from ipware import get_client_ip

from passbook.core.models import Policy, User
from passbook.policy.struct import PolicyRequest, PolicyResult


class SuspiciousRequestPolicy(Policy):
    """Return true if request IP/target username's score is below a certain threshold"""

    check_ip = models.BooleanField(default=True)
    check_username = models.BooleanField(default=True)
    threshold = models.IntegerField(default=-5)

    form = 'passbook.suspicious_policy.forms.SuspiciousRequestPolicyForm'

    def passes(self, request: PolicyRequest) -> PolicyResult:
        remote_ip, _ = get_client_ip(request.http_request)
        passing = True
        if self.check_ip:
            ip_scores = IPScore.objects.filter(ip=remote_ip, score__lte=self.threshold)
            passing = passing and ip_scores.exists()
        if self.check_username:
            user_scores = UserScore.objects.filter(user=request.user, score__lte=self.threshold)
            passing = passing and user_scores.exists()
        return PolicyResult(passing)

    class Meta:

        verbose_name = _('Suspicious Request Policy')
        verbose_name_plural = _('Suspicious Request Policies')

class IPScore(models.Model):
    """Store score coming from the same IP"""

    ip = models.GenericIPAddressField(unique=True)
    score = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "IPScore for %s @ %d" % (self.ip, self.score)

class UserScore(models.Model):
    """Store score attempting to log in as the same username"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "UserScore for %s @ %d" % (self.user, self.score)
