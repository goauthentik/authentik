"""SAML Source tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from lxml.etree import XMLSyntaxError  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.metadata import MetadataFetchError, fetch_metadata
from authentik.events.models import Event, EventAction
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.metadata_parser import IdentityProviderMetadataParser
from authentik.tasks.middleware import CurrentTask

LOGGER = get_logger()


@actor(description=_("Update SAML sources' settings from their metadata URL."))
def update_saml_source_metadata(source_pk: str | None = None):
    """Re-fetch the Identity Provider metadata of sources with a metadata URL and apply any
    changes. Updates a single source when `source_pk` is given, otherwise all of them."""
    self = CurrentTask.get_task()
    sources = SAMLSource.objects.exclude(metadata_url="")
    if source_pk is not None:
        sources = sources.filter(pk=source_pk)
        if not sources.exists():
            self.info(f"Source {source_pk} not found or has no metadata URL, skipping.")
            return
    for source in sources:
        _fetch_and_apply_metadata(self, source)


def _fetch_and_apply_metadata(task, source: SAMLSource):
    """Fetch, parse and apply the metadata of a single source"""
    try:
        raw_metadata = fetch_metadata(source.metadata_url)
        metadata = IdentityProviderMetadataParser().parse(raw_metadata)
        changed = metadata.apply_to_source(source)
    except (MetadataFetchError, ValueError, KeyError, XMLSyntaxError) as exc:
        LOGGER.warning("Failed to update source from metadata", source=source, exc=exc)
        task.warning(f"Failed to update source {source.name} from metadata: {exc}")
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            source=source,
            message=f"Failed to update SAML source from metadata URL: {exc}",
        ).save()
        return
    if not changed:
        task.info(f"Metadata for source {source.name} is unchanged.")
        return
    source.save()
    task.info(f"Updated source {source.name} from metadata.")
