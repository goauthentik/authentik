"""authentik core source form fields"""

SOURCE_FORM_FIELDS = [
    "name",
    "slug",
    "enabled",
    "authentication_flow",
    "enrollment_flow",
]
SOURCE_SERIALIZER_FIELDS = [
    "pk",
    "name",
    "slug",
    "enabled",
    "authentication_flow",
    "enrollment_flow",
    "verbose_name",
    "verbose_name_plural",
]
