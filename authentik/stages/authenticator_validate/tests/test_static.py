from threading import Thread

from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.test.client import RequestFactory

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_static.models import StaticDevice
from authentik.stages.authenticator_validate.challenge import ChallengeValidationError, FlowContext
from authentik.stages.authenticator_validate.challenge.static import StaticChallenger
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses


class StaticChallengerMultiDeviceTests(TestCase):
    """Validation behavior of StaticChallenger when the user has more than
    one StaticDevice."""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()
        self.stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            device_classes=[DeviceClasses.STATIC],
            static_otp_throttling_factor=0,
        )

    def _challenger(self) -> StaticChallenger:
        return StaticChallenger(self.request_factory.get("/"), self.stage, FlowContext())

    def test_validate_picks_matching_device_among_many(self):
        """validate() iterates the queryset and returns the device whose
        token_set contains the supplied token."""
        device_a = self.user.staticdevice_set.create()
        device_b = self.user.staticdevice_set.create()
        device_c = self.user.staticdevice_set.create()
        device_a.token_set.create(token=generate_id(length=16))
        device_c.token_set.create(token=generate_id(length=16))
        valid = generate_id(length=16)
        device_b.token_set.create(token=valid)

        matched = self._challenger().validate(
            StaticDevice.objects.filter(user=self.user), {}, valid
        )

        self.assertEqual(matched.pk, device_b.pk)
        # Matching token consumed.
        self.assertFalse(device_b.token_set.filter(token=valid).exists())
        # Other devices' tokens untouched.
        self.assertEqual(device_a.token_set.count(), 1)
        self.assertEqual(device_c.token_set.count(), 1)

    def test_validate_no_match_raises(self):
        """When no device in the queryset accepts the token, validate()
        raises ChallengeValidationError."""
        device_a = self.user.staticdevice_set.create()
        device_b = self.user.staticdevice_set.create()
        device_a.token_set.create(token=generate_id(length=16))
        device_b.token_set.create(token=generate_id(length=16))

        with self.assertRaises(ChallengeValidationError):
            self._challenger().validate(
                StaticDevice.objects.filter(user=self.user), {}, "not-a-real-token"
            )

    def test_validate_empty_queryset_raises_challenge_validation_error(self):
        """If the device queryset is empty (e.g., the user's only device was
        deleted between challenge issuance and submission), validate() must
        raise ChallengeValidationError"""
        with self.assertRaises(ChallengeValidationError):
            self._challenger().validate(StaticDevice.objects.filter(user=self.user), {}, "anything")


class StaticChallengerConcurrencyTests(TransactionTestCase):
    """A single-use static token must not be consumed by more than one
    concurrent validate() call, even when the queryset spans multiple
    devices."""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()
        self.stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            device_classes=[DeviceClasses.STATIC],
            static_otp_throttling_factor=0,
        )
        self.valid = generate_id(length=16)
        # Two devices; the valid token lives in the second so iteration is
        # exercised, not just a single-row select_for_update.
        self.user.staticdevice_set.create()
        winning_device = self.user.staticdevice_set.create()
        winning_device.token_set.create(token=self.valid)

    def test_only_one_thread_consumes_token(self):
        request_factory = self.request_factory
        stage = self.stage
        user = self.user
        token = self.valid

        class ValidateThread(Thread):
            __test__ = False

            def __init__(self):
                super().__init__()
                self.matched: StaticDevice | None = None
                self.error: Exception | None = None

            def run(self):
                challenger = StaticChallenger(request_factory.get("/"), stage, FlowContext())
                try:
                    self.matched = challenger.validate(
                        StaticDevice.objects.filter(user=user), {}, token
                    )
                except ChallengeValidationError as exc:
                    self.error = exc
                finally:
                    connection.close()

        threads = [ValidateThread() for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        succeeded = [t for t in threads if t.matched is not None]
        self.assertEqual(len(succeeded), 1)
        # All other threads must have raised ChallengeValidationError, not
        # some unrelated exception.
        for thread in threads:
            if thread.matched is None:
                self.assertIsInstance(thread.error, ChallengeValidationError)
