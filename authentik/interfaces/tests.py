"""Interface tests"""
from django.test import RequestFactory

from authentik.interfaces.models import InterfaceType
from authentik.interfaces.views import reverse_interface as full_reverse_interface


def reverse_interface(interface_type: InterfaceType, **kwargs):
    """reverse_interface wrapper for tests"""
    factory = RequestFactory()
    request = factory.get("/")
    return full_reverse_interface(request, interface_type, **kwargs)
