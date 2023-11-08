from rest_framework.fields import HiddenField


class CurrentTenantDefault:
    requires_context = True

    def __call__(self, serializer_field):
        request = serializer_field.context.get("request", None)
        if not request:
            return None
        return request.tenant

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class TenantSerializer:
    tenant = HiddenField(default=CurrentTenantDefault())
