from django.db.models import QuerySet
from django_dramatiq_postgres.broker import PostgresBroker
from structlog.stdlib import get_logger

LOGGER = get_logger()


class Broker(PostgresBroker):
    @property
    def query_set(self) -> QuerySet:
        return super().query_set.select_related("tenant").filter(tenant__ready=True)
