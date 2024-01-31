from django.utils.translation import gettext as __
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField

from authentik.core.models import Application
from authentik.core.signals import login_failed
from authentik.events.models import Event, EventAction
from authentik.flows.challenge import Challenge
from authentik.flows.views.executor import SESSION_KEY_APPLICATION_PRE
from authentik.lib.utils.errors import exception_to_string
from authentik.stages.authenticator.validate import (
    DeviceChallenge,
    DeviceChallengeResponse,
    DeviceValidator,
)
from authentik.stages.authenticator_mobile.models import (
    ItemMatchingMode,
    MobileDevice,
    MobileTransaction,
    TransactionStates,
)
from authentik.stages.authenticator_mobile.stage import SESSION_KEY_MOBILE_TRANSACTION
from authentik.stages.authenticator_validate.models import DeviceClasses


class MobileDeviceChallenge(DeviceChallenge):
    component = CharField(default="ak-stage-authenticator-validate-device-mobile")
    item_mode = ChoiceField(choices=ItemMatchingMode.choices)
    item = CharField()


class MobileDeviceChallengeResponse(DeviceChallengeResponse[MobileDevice]):
    component = CharField(default="ak-stage-authenticator-validate-device-mobile")

    def validate(self, attrs: dict) -> dict:
        user = self.stage.get_pending_user()
        if self.device.user != user:
            self.stage.logger.warning("device mismatch")
            raise ValidationError("Invalid device")

        transaction: MobileTransaction = self.stage.request.session[SESSION_KEY_MOBILE_TRANSACTION]

        try:
            status = transaction.check_response()
            if status == TransactionStates.WAIT:
                raise ValidationError("Waiting for push answer")
            self.stage.request.session.delete(SESSION_KEY_MOBILE_TRANSACTION)
            if status == TransactionStates.DENY:
                self.stage.logger.debug("mobile push response", result=status)
                login_failed.send(
                    sender=__name__,
                    credentials={"username": user.username},
                    request=self.stage.request,
                    stage=self.stage.executor.current_stage,
                    device_class=DeviceClasses.MOBILE.value,
                    mobile_response=status,
                )
                raise ValidationError("Mobile denied access", code="denied")
            return super().validate(attrs)
        except TimeoutError:
            raise ValidationError("Mobile push notification timed out.")
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to Mobile authenticate user: {str(exc)}",
                user=user,
            ).from_http(self.stage.request, user)
            raise ValidationError("Mobile denied access", code="denied")


class MobileDeviceValidator(DeviceValidator[MobileDevice]):
    response_class = MobileDeviceChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        self.request.session.pop(SESSION_KEY_MOBILE_TRANSACTION, None)
        transaction = self.device.create_transaction()
        self.request.session[SESSION_KEY_MOBILE_TRANSACTION] = transaction
        return MobileDeviceChallenge(
            data={
                "item_mode": transaction.device.stage.item_matching_mode,
                "item": transaction.correct_item,
            }
        )

    def select_challenge(self):
        # Get additional context for push
        push_context = {
            __("Domain"): self.request.get_host(),
        }
        if SESSION_KEY_APPLICATION_PRE in self.request.session:
            push_context[__("Application")] = self.request.session.get(
                SESSION_KEY_APPLICATION_PRE, Application()
            ).name
        if SESSION_KEY_MOBILE_TRANSACTION not in self.request.session:
            raise ValidationError()

        try:
            transaction: MobileTransaction = self.request.session.get(
                SESSION_KEY_MOBILE_TRANSACTION
            )
            if not transaction.send_message(self.request, **push_context):
                raise ValidationError("Failed to send push notification", code="internal")
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="Failed to Mobile authenticate user",
                exception=exception_to_string(exc),
                user=self.device.user,
            ).from_http(self.request, self.device.user)
            raise ValidationError("Mobile denied access", code="denied")
