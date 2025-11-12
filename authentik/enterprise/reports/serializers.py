from rest_framework.fields import CharField, IntegerField, SerializerMethodField

from authentik.core.api.users import UserSerializer
from authentik.core.models import User
from authentik.events.api.events import EventSerializer


class ExportUserSerializer(UserSerializer):
    """Serializer for exporting users"""

    groups = SerializerMethodField(source="get_groups")

    def get_groups(self, instance: User) -> str:
        return ",".join([group.name for group in instance.ak_groups.all()])

    class Meta(UserSerializer.Meta):
        fields = [
            f for f in UserSerializer.Meta.fields if f not in {"groups_obj", "is_superuser"}
        ] + ["groups"]


class ExportEventSerializer(EventSerializer):
    """Serializer for exporting events"""

    user_pk = IntegerField(source="user.pk", read_only=True)
    username = CharField(source="user.username", read_only=True)
    email = CharField(source="user.email", read_only=True)

    class Meta(EventSerializer.Meta):
        fields = [f for f in EventSerializer.Meta.fields if f != "user"] + [
            "user_pk",
            "username",
            "email",
        ]
