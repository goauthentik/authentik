"""Base authenticator models"""

from datetime import timedelta
from typing import Any

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django.utils.functional import cached_property

from authentik.core.models import User
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.models import CreatedUpdatedModel
from authentik.stages.authenticator.util import random_number_token


class DeviceManager(models.Manager):
    """Manager for devices"""

    def devices_for_user(self, user: User, confirmed: bool | None = None):
        """All devices of this class for a user, optionally filtered by `confirmed`"""
        devices = self.model.objects.filter(user=user)
        if confirmed is not None:
            devices = devices.filter(confirmed=bool(confirmed))

        return devices


class Device(CreatedUpdatedModel):
    """Abstract base model for an authenticator device attached to a user.
    Devices are stateful and must be saved before they can be used."""

    user = models.ForeignKey(
        User,
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=64, help_text="The human-readable name of this device.")

    confirmed = models.BooleanField(default=True, help_text="Is this device ready for use?")

    last_used = models.DateTimeField(null=True)

    objects = DeviceManager()

    def get_challenge_for_device(
        self, request: HttpRequest, executor: FlowExecutorView
    ) -> dict[str, Any]:
        return {}

    def select_challenge(self, request: HttpRequest): ...

    def validate_challenge(
        self,
        request: HttpRequest,
        input: Any,
        executor: FlowExecutorView,
        user: User,
    ): ...

    class Meta:
        abstract = True

    def __str__(self):
        try:
            user = self.user
        except ObjectDoesNotExist:
            user = None

        return f"{self.name} ({user})"

    @property
    def persistent_id(self):
        """A stable device identifier for forms and APIs."""
        return f"{self.model_label()}/{self.id}"

    @classmethod
    def model_label(cls):
        """Model label in the form `<app_label>.<model_name>`"""
        return f"{cls._meta.app_label}.{cls._meta.model_name}"

    @classmethod
    def from_persistent_id(cls, persistent_id, for_verify=False):
        """Load a device from its persistent_id. With `for_verify`, the device is
        locked with select_for_update, so this must be called inside a transaction."""
        device = None

        try:
            model_label, device_id = persistent_id.rsplit("/", 1)
            app_label, model_name = model_label.split(".")

            device_cls = apps.get_model(app_label, model_name)
            if issubclass(device_cls, Device):
                device_set = device_cls.objects.filter(id=int(device_id))
                if for_verify:
                    device_set = device_set.select_for_update()
                device = device_set.first()
        except ValueError, LookupError:
            pass

        return device

    def is_interactive(self):
        """Check if this device is interactive, i.e. overrides `generate_challenge`"""
        return not hasattr(self.generate_challenge, "stub")

    def generate_challenge(self):
        """Generate a challenge the user needs to produce a token. May have side effects
        such as sending a message. Returns a message for the user, or None."""
        return None

    generate_challenge.stub = True

    def verify_is_allowed(self):
        """Check if `verify_token` may be called. Returns `(True, None)` if allowed,
        otherwise `(False, data)` with details such as a `VerifyNotAllowed` reason."""
        return (True, None)

    def verify_token(self, token):
        """Verify a token. A token should no longer be valid once this returns True."""
        return False


class SideChannelDevice(Device):
    """Abstract base model for a side-channel device. Implements token generation,
    verification and expiry; subclasses only implement delivery."""

    token = models.CharField(max_length=16, blank=True, null=True)

    valid_until = models.DateTimeField(
        default=timezone.now,
        help_text="The timestamp of the moment of expiry of the saved token.",
    )

    class Meta:
        abstract = True

    def generate_token(self, length=6, valid_secs=300, commit=True):
        """Generate a token valid for `valid_secs` seconds"""
        self.token = random_number_token(length)
        self.valid_until = timezone.now() + timedelta(seconds=valid_secs)
        if commit:
            self.save()

    def verify_token(self, token):
        """Verify a token by content and expiry, clearing it on success"""
        _now = timezone.now()

        if (self.token is not None) and (token == self.token) and (_now < self.valid_until):
            self.token = None
            self.valid_until = _now
            self.save()

            return True
        return False


class VerifyNotAllowed:
    """Reasons returned by `Device.verify_is_allowed`"""

    N_FAILED_ATTEMPTS = "N_FAILED_ATTEMPTS"


class ThrottlingMixin(models.Model):
    """Exponential back-off for token verification. Subclasses must call
    `verify_is_allowed`, `throttle_reset` and `throttle_increment` from `verify_token`."""

    throttling_failure_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        help_text=(
            "A timestamp of the last failed verification attempt. "
            "Null if last attempt succeeded."
        ),
    )

    throttling_failure_count = models.PositiveIntegerField(
        default=0, help_text="Number of successive failed attempts."
    )

    class Meta:
        abstract = True

    def verify_is_allowed(self):
        """Disallow verification until the back-off delay has passed"""
        if (
            self.throttling_enabled
            and self.throttling_failure_count > 0
            and self.throttling_failure_timestamp is not None
        ):
            now = timezone.now()
            delay = (now - self.throttling_failure_timestamp).total_seconds()
            # Required delays should be 1, 2, 4, 8 ...
            delay_required = self.get_throttle_factor() * (2 ** (self.throttling_failure_count - 1))
            if delay < delay_required:
                return (
                    False,
                    {
                        "reason": VerifyNotAllowed.N_FAILED_ATTEMPTS,
                        "failure_count": self.throttling_failure_count,
                        "locked_until": self.throttling_failure_timestamp
                        + timedelta(seconds=delay_required),
                    },
                )

        return super().verify_is_allowed()

    def throttle_reset(self, commit=True):
        """Reset throttling, usually after a successful attempt"""
        self.throttling_failure_timestamp = None
        self.throttling_failure_count = 0
        if commit:
            self.save()

    def throttle_increment(self, commit=True):
        """Increase throttling, usually after a failed attempt"""
        self.throttling_failure_timestamp = timezone.now()
        self.throttling_failure_count += 1
        if commit:
            self.save()

    @cached_property
    def throttling_enabled(self) -> bool:
        """Check if throttling is enabled"""
        return self.get_throttle_factor() > 0

    def get_throttle_factor(self) -> float:  # pragma: no cover
        """Get the throttle factor"""
        return getattr(self, "_throttle_factor", 1.0)

    def set_throttle_factor(self, throttle_factor: float) -> None:
        """Set the throttle factor. Delays are `factor * 2^(failures - 1)` seconds;
        a factor of 0 disables throttling."""
        self._throttle_factor = throttle_factor
