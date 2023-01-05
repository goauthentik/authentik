"""user set password meta model"""
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, JSONField
from structlog.stdlib import get_logger

from authentik.blueprints.v1.meta.registry import BaseMetaModel, MetaResult, registry
from authentik.core.api.utils import PassiveSerializer, is_dict
from authentik.core.models import User

LOGGER = get_logger()


class UserSetPasswordMetaSerializer(PassiveSerializer):
    """Serializer for meta user set password model"""

    user_identifiers = JSONField(validators=[is_dict])
    raw_password = CharField()
    set_unusable = BooleanField(default=False)

    # We cannot override `instance` as that will confuse rest_framework
    # and make it attempt to update the instance
    user_instance: "User"

    def validate(self, attrs):
        user_identifiers = attrs["user_identifiers"]
        instance = User.objects.filter(**user_identifiers).first()
        if not instance:
            raise ValidationError("User does not exist")
        self.user_instance = instance
        return super().validate(attrs)

    def create(self, validated_data: dict) -> MetaResult:
        if not self.user_instance:
            LOGGER.info("user_identifiers")
            return MetaResult()
        LOGGER.debug("Setting user password", user=self.user_instance)
        if validated_data["set_unusable"]:
            self.user_instance.set_unusable_password()
        else:
            self.user_instance.set_password(validated_data["raw_password"])
        self.user_instance.save()
        return MetaResult()


@registry.register("metausersetpassword")
class MetaUserSetPassword(BaseMetaModel):
    """Meta model to set a user's password"""

    @staticmethod
    def serializer() -> UserSetPasswordMetaSerializer:
        return UserSetPasswordMetaSerializer

    class Meta:

        abstract = True
