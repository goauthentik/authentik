from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.models import DeviceUser


class DeviceUserSerializer(ModelSerializer):

    user_obj = UserSerializer(source="user", read_only=True)

    class Meta:
        model = DeviceUser
        fields = [
            "is_primary",
            "device",
            "user",
            "user_obj",
        ]
