"""authentik sessions engine"""

import pickle

from django.contrib.sessions.backends.db import SessionStore as SessionBase
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.utils.functional import cached_property
from structlog.stdlib import get_logger

LOGGER = get_logger()


class SessionStore(SessionBase):
    def __init__(self, session_key=None, **create_kwargs):
        super().__init__(session_key)
        self._create_kwargs = create_kwargs

    @classmethod
    def get_model_class(cls):
        from authentik.core.models import Session

        return Session

    @cached_property
    def model_fields(self):
        return [k.value for k in self.model.Keys]

    def _get_session_from_db(self):
        try:
            return self.model.objects.get(
                session_key=self.session_key,
                expires__gt=timezone.now(),
            )
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
            self._session_key = None

    async def _aget_session_from_db(self):
        try:
            return await self.model.objects.aget(
                session_key=self.session_key,
                expires__gt=timezone.now(),
            )
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
            self._session_key = None

    def encode(self, session_dict):
        return pickle.dumps(session_dict, protocol=pickle.HIGHEST_PROTOCOL)

    def decode(self, session_data):
        try:
            return pickle.loads(session_data)
        except Exception:
            # ValueError, unpickling exceptions. If any of these happen, just return an empty
            # dictionary (an empty session)
            pass
        return {}

    def load(self):
        s = self._get_session_from_db()
        if s:
            # TODO: automate
            return {
                "last_ip": s.last_ip,
                "last_user_agent": s.last_user_agent,
                "last_used": s.last_used,
                "authenticatedsession": getattr(s, "authenticatedsession", None),
                **self.decode(s.session_data),
            }
        else:
            return {}

    async def aload(self):
        s = await self._aget_session_from_db()
        if s:
            # TODO: automate
            return {
                "last_ip": s.last_ip,
                "last_user_agent": s.last_user_agent,
                "last_used": s.last_used,
                "authenticatedsession": getattr(s, "authenticatedsession", None),
                **self.decode(s.session_data),
            }
        else:
            return {}

    def create_model_instance(self, data):
        args = {
            "session_key": self._get_or_create_session_key(),
            "expires": self.get_expiry_date(),
            "session_data": {},
            **self._create_kwargs,
        }
        for k, v in data.items():
            if k in self.model_fields:
                args[k] = v
            elif k == "authenticatedsession":
                pass
            else:
                args["session_data"][k] = v
        args["session_data"] = self.encode(args["session_data"])
        return self.model(**args)

    async def acreate_model_instance(self, data):
        args = {
            "session_key": await self._aget_or_create_session_key(),
            "expires": await self.aget_expiry_date(),
            "session_data": {},
            **self._create_kwargs,
        }
        for k, v in data.items():
            if k in self.model_fields:
                args[k] = v
            elif k == "authenticatedsession":
                pass
            else:
                args["session_data"][k] = v
        args["session_data"] = self.encode(args["session_data"])
        return self.model(**args)

    @classmethod
    def clear_expired(cls):
        cls.get_model_class().objects.filter(expires__lt=timezone.now()).delete()

    @classmethod
    async def aclear_expired(cls):
        await cls.get_model_class().objects.filter(expires__lt=timezone.now()).adelete()
