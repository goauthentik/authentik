from rest_framework import serializers
from enum import IntFlag


class ChallengeCapabilities(IntFlag):
    """Capabilities a client can have, Bitwise combined."""

    # Standard Password Input. Note that this is only a single Input, and does not apply
    # to TOTP for example
    Password = 1
    # Client that can wait, i.e. for Notification-based 2FA like Authy.
    Wait = 2
    # Client supports additional (Text for totp, for example)
    AuxiliaryInput = 4

    # This is a special capability that is only possible in the HTML Frontend.
    JSLoading = 100


class InitiateFlowExecutionSerializer(serializers.Serializer):
    # TODO: write current instance in session

    capabilities = serializers.IntegerField(required=True)
    user_identifier = serializers.CharField()


class ChallengeRequestSerializer(serializers.Serializer):
    pass


class ChallengeResponseSerializer(serializers.Serializer):
    pass
