from django.core.exceptions import SuspiciousOperation
from django.contrib.sessions.backends.cached_db import SessionStore as SessionBase
from django.utils import timezone
from structlog.stdlib import get_logger

LOGGER = get_logger()


class SessionStore(SessionBase):
    cache_key_prefix = "goauthentik.io/core/sessions/"

    @classmethod
    def get_model_class(cls):
        from authentik.core.models import Session

        return Session

    def _get_session_from_db(self):
        try:
            return self.model.objects.get(session_key=self.session_key, expires__gt=timezone.now())
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(
                    "suspicious operation while retrieving session from database", exc=exc
                )
            self._session_key = None

    async def _aget_session_from_db(self):
        try:
            return await self.model.objects.aget(
                session_key=self.session_key, expires__gt=timezone.now()
            )
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(
                    "suspicious operation while retrieving session from database", exc=exc
                )
            self._session_key = None

    def create_model_instance(self, data):
        return self.model(
            session_key=self._get_or_create_session_key(),
            session_data=self.encode(data),
            expires=self.get_expiry_date(),
        )

    async def acreate_model_instance(self, data):
        return self.model(
            session_key=await self._aget_or_create_session_key(),
            session_data=self.encode(data),
            expires=await self.aget_expiry_date(),
        )

    @classmethod
    def clear_expired(cls):
        LOGGER.warning(
            "Not clearing expired sessions. Trigger the clean_expired_models system task instead."
        )

    @classmethod
    async def aclear_expired(cls):
        LOGGER.warning(
            "Not clearing expired sessions. Trigger the clean_expired_models system task instead."
        )
