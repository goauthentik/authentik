"""authentik sessions engine"""

from django.core.exceptions import SuspiciousOperation
from django.contrib.sessions.backends.db import SessionStore as SessionBase
from django.utils import timezone
from structlog.stdlib import get_logger

LOGGER = get_logger()


class SessionStore(SessionBase):
    @classmethod
    def get_model_class(cls):
        from authentik.core.models import Session

        return Session

    def _get_session_from_db(self):
        try:
            return self.model.objects.select_related(
                "authenticatedsession", "authenticatedsession__user"
            ).get(session_key=self.session_key, expires__gt=timezone.now())
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(
                    "suspicious operation while retrieving session from database", exc=exc
                )
            self._session_key = None

    async def _aget_session_from_db(self):
        try:
            return await self.model.objects.select_related(
                "authenticatedsession", "authenticatedsession__user"
            ).aget(session_key=self.session_key, expires__gt=timezone.now())
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(
                    "suspicious operation while retrieving session from database", exc=exc
                )
            self._session_key = None

    def load(self):
        self._session_obj = self._get_session_from_db()
        return self.decode(self._session_obj.session_data) if self._session_obj else {}

    async def aload(self):
        self._session_obj = await self._aget_session_from_db()
        return self.decode(self._session_obj.session_data) if self._session_obj else {}

    @classmethod
    def from_session_obj(cls, session):
        s = cls(session.session_data)
        s._session_obj = session
        s.accessed = True
        s._session_cache = s.decode(s._session_obj.session_data)
        return s

    def _get_session_obj(self):
        # Make sure session is loaded
        _s = self._session
        return self._session_obj

    session_obj = property(_get_session_obj)

    def _get_authenticated_session(self):
        # Make sure session is loaded
        _s = self._session
        try:
            return self._session_obj.authenticatedsession
        except AttributeError:
            return None

    authenticated_session = property(_get_authenticated_session)

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
