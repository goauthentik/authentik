"""Registers and loads Processor classes from settings."""
from logging import getLogger

from passbook.lib.utils.reflection import path_to_class
from passbook.saml_idp.exceptions import CannotHandleAssertion
from passbook.saml_idp.models import SAMLProvider

LOGGER = getLogger(__name__)


def get_processor(remote):
    """Get an instance of the processor with config."""
    proc = path_to_class(remote.processor_path)
    return proc(remote)


def find_processor(request):
    """Returns the Processor instance that is willing to handle this request."""
    for remote in SAMLProvider.objects.all():
        proc = get_processor(remote)
        try:
            if proc.can_handle(request):
                return proc, remote
        except CannotHandleAssertion as exc:
            # Log these, but keep looking.
            LOGGER.debug('%s %s', proc, exc)

    raise CannotHandleAssertion('No Processors to handle this request.')
