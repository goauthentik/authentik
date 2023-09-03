"""Base authenticator models"""
from datetime import timedelta

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from authentik.core.models import User
from authentik.stages.authenticator.util import random_number_token


class DeviceManager(models.Manager):
    """
    The :class:`~django.db.models.Manager` object installed as
    ``Device.objects``.
    """

    def devices_for_user(self, user, confirmed=None):
        """
        Returns a queryset for all devices of this class that belong to the
        given user.

        :param user: The user.
        :type user: :class:`~django.contrib.auth.models.User`

        :param confirmed: If ``None``, all matching devices are returned.
            Otherwise, this can be any true or false value to limit the query
            to confirmed or unconfirmed devices, respectively.
        """
        devices = self.model.objects.filter(user=user)
        if confirmed is not None:
            devices = devices.filter(confirmed=bool(confirmed))

        return devices


class Device(models.Model):
    """
    Abstract base model for a :term:`device` attached to a user. Plugins must
    subclass this to define their OTP models.

    .. _unsaved_device_warning:

    .. warning::

        OTP devices are inherently stateful. For example, verifying a token is
        logically a mutating operation on the device, which may involve
        incrementing a counter or otherwise consuming a token. A device must be
        committed to the database before it can be used in any way.

    .. attribute:: user

        *ForeignKey*: Foreign key to your user model, as configured by
        :setting:`AUTH_USER_MODEL` (:class:`~django.contrib.auth.models.User`
        by default).

    .. attribute:: name

        *CharField*: A human-readable name to help the user identify their
        devices.

    .. attribute:: confirmed

        *BooleanField*: A boolean value that tells us whether this device has
        been confirmed as valid. It defaults to ``True``, but subclasses or
        individual deployments can force it to ``False`` if they wish to create
        a device and then ask the user for confirmation. As a rule, built-in
        APIs that enumerate devices will only include those that are confirmed.

    .. attribute:: objects

        A :class:`~authentik.stages.authenticator.models.DeviceManager`.
    """

    user = models.ForeignKey(
        User,
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=64, help_text="The human-readable name of this device.")

    confirmed = models.BooleanField(default=True, help_text="Is this device ready for use?")

    objects = DeviceManager()

    class Meta:
        abstract = True

    def __str__(self):
        try:
            user = self.user
        except ObjectDoesNotExist:
            user = None

        return "{0} ({1})".format(self.name, user)

    @property
    def persistent_id(self):
        """
        A stable device identifier for forms and APIs.
        """
        return "{0}/{1}".format(self.model_label(), self.id)

    @classmethod
    def model_label(cls):
        """
        Returns an identifier for this Django model class.

        This is just the standard "<app_label>.<model_name>" form.

        """
        return "{0}.{1}".format(cls._meta.app_label, cls._meta.model_name)

    @classmethod
    def from_persistent_id(cls, persistent_id, for_verify=False):
        """
        Loads a device from its persistent id::

            device == Device.from_persistent_id(device.persistent_id)

        :param bool for_verify: If ``True``, we'll load the device with
            :meth:`~django.db.models.query.QuerySet.select_for_update` to
            prevent concurrent verifications from succeeding. In which case,
            this must be called inside a transaction.

        """
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
        except (ValueError, LookupError):
            pass

        return device

    def is_interactive(self):
        """
        Returns ``True`` if this is an interactive device. The default
        implementation returns ``True`` if
        :meth:`~authentik.stages.authenticator.models.Device.generate_challenge` has been
        overridden, but subclasses are welcome to provide smarter
        implementations.

        :rtype: bool
        """
        return not hasattr(self.generate_challenge, "stub")

    def generate_challenge(self):
        """
        Generates a challenge value that the user will need to produce a token.
        This method is permitted to have side effects, such as transmitting
        information to the user through some other channel (email or SMS,
        perhaps). And, of course, some devices may need to commit the
        challenge to the database.

        :returns: A message to the user. This should be a string that fits
            comfortably in the template ``'OTP Challenge: {0}'``. This may
            return ``None`` if this device is not interactive.
        :rtype: string or ``None``

        :raises: Any :exc:`~exceptions.Exception` is permitted. Callers should
            trap ``Exception`` and report it to the user.
        """
        return None

    generate_challenge.stub = True

    def verify_is_allowed(self):
        """
        Checks whether it is permissible to call :meth:`verify_token`. If it is
        allowed, returns ``(True, None)``. Otherwise returns ``(False,
        data_dict)``, where ``data_dict`` contains extra information, defined
        by the implementation.

        This method can be used to implement throttling or locking, for
        example. Client code should check this method before calling
        :meth:`verify_token` and report problems to the user.

        To report specific problems, the data dictionary can return include a
        ``'reason'`` member with a value from the constants in
        :class:`VerifyNotAllowed`. Otherwise, an ``'error_message'`` member
        should be provided with an error message.

        :meth:`verify_token` should also call this method and return False if
        verification is not allowed.

        :rtype: (bool, dict or ``None``)

        """
        return (True, None)

    def verify_token(self, token):
        """
        Verifies a token. As a rule, the token should no longer be valid if
        this returns ``True``.

        :param str token: The OTP token provided by the user.
        :rtype: bool
        """
        return False


class SideChannelDevice(Device):
    """
    Abstract base model for a side-channel :term:`device` attached to a user.

    This model implements token generation, verification and expiration, so the
    concrete devices only have to implement delivery.

    """

    token = models.CharField(max_length=16, blank=True, null=True)

    valid_until = models.DateTimeField(
        default=timezone.now,
        help_text="The timestamp of the moment of expiry of the saved token.",
    )

    class Meta:
        abstract = True

    def generate_token(self, length=6, valid_secs=300, commit=True):
        """
        Generates a token of the specified length, then sets it on the model
        and sets the expiration of the token on the model.

        Pass 'commit=False' to avoid calling self.save().

        :param int length: Number of decimal digits in the generated token.
        :param int valid_secs: Amount of seconds the token should be valid.
        :param bool commit: Whether to autosave the generated token.

        """
        self.token = random_number_token(length)
        self.valid_until = timezone.now() + timedelta(seconds=valid_secs)
        if commit:
            self.save()

    def verify_token(self, token):
        """
        Verifies a token by content and expiry.

        On success, the token is cleared and the device saved.

        :param str token: The OTP token provided by the user.
        :rtype: bool

        """
        _now = timezone.now()

        if (self.token is not None) and (token == self.token) and (_now < self.valid_until):
            self.token = None
            self.valid_until = _now
            self.save()

            return True
        return False


class VerifyNotAllowed:
    """
    Constants that may be returned in the ``reason`` member of the extra
    information dictionary returned by
    :meth:`~authentik.stages.authenticator.models.Device.verify_is_allowed`

    .. data:: N_FAILED_ATTEMPTS

       Indicates that verification is disallowed because of ``n`` successive
       failed attempts. The data dictionary should include the value of ``n``
       in member ``failure_count``

    """

    N_FAILED_ATTEMPTS = "N_FAILED_ATTEMPTS"


class ThrottlingMixin(models.Model):
    """
    Mixin class for models that want throttling behaviour.

    This implements exponential back-off for verifying tokens. Subclasses must
    implement :meth:`get_throttle_factor`, and must use the
    :meth:`verify_is_allowed`, :meth:`throttle_reset` and
    :meth:`throttle_increment` methods from within their verify_token() method.

    See the implementation of
    :class:`~authentik.stages.authenticator.plugins.otp_email.models.EmailDevice` for an example.

    """

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

    def verify_is_allowed(self):
        """
        If verification is allowed, returns ``(True, None)``.
        Otherwise, returns ``(False, data_dict)``.

        ``data_dict`` contains further information. Currently it can be::

            {
                'reason': VerifyNotAllowed.N_FAILED_ATTEMPTS,
                'failure_count': n
            }

        where ``n`` is the number of successive failures. See
        :class:`~authentik.stages.authenticator.models.VerifyNotAllowed`.

        """
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
        """
        Call this method to reset throttling (normally when a verify attempt
        succeeded).

        Pass 'commit=False' to avoid calling self.save().

        """
        self.throttling_failure_timestamp = None
        self.throttling_failure_count = 0
        if commit:
            self.save()

    def throttle_increment(self, commit=True):
        """
        Call this method to increase throttling (normally when a verify attempt
        failed).

        Pass 'commit=False' to avoid calling self.save().

        """
        self.throttling_failure_timestamp = timezone.now()
        self.throttling_failure_count += 1
        if commit:
            self.save()

    @cached_property
    def throttling_enabled(self) -> bool:
        """Check if throttling is enabled"""
        return self.get_throttle_factor() > 0

    def get_throttle_factor(self):  # pragma: no cover
        """
        This must be implemented to return the throttle factor.

        The number of seconds required between verification attempts will be
        :math:`c2^{n-1}` where `c` is this factor and `n` is the number of
        previous failures. A factor of 1 translates to delays of 1, 2, 4, 8,
        etc. seconds. A factor of 0 disables the throttling.

        Normally this is just a wrapper for a plugin-specific setting like
        :setting:`OTP_EMAIL_THROTTLE_FACTOR`.

        """
        raise NotImplementedError()

    class Meta:
        abstract = True
