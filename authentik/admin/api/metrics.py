"""authentik administration metrics"""


from rest_framework.fields import IntegerField

from authentik.core.api.utils import PassiveSerializer


class CoordinateSerializer(PassiveSerializer):
    """Coordinates for diagrams"""

    x_cord = IntegerField(read_only=True)
    y_cord = IntegerField(read_only=True)
