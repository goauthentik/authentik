from django.contrib.sessions.backends.db import SessionStore as BaseSessionStore
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from structlog import get_logger

LOGGER = get_logger()


class SessionStore(BaseSessionStore):
    @classmethod
    def get_model_class(cls):
        from authentik.core.models import AuthenticatedSession

        return AuthenticatedSession

    def _get_session_from_db(self):
        try:
            return self.model.objects.get(session_key=self.session_key, expires__gt=timezone.now())
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
            self._session_key = None

    async def _aget_session_from_db(self):
        try:
            return self.model.objects.aget(session_key=self.session_key, expires__gt=timezone.now())
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
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
        cls.get_model_class().objects.filter(expires__lt=timezone.now()).delete()

    @classmethod
    async def aclear_expired(cls):
        await cls.get_model_class().objects.filter(expires__lt=timezone.now()).adelete()
