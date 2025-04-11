"""authentik sessions engine"""

import pickle  # nosec

from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore as SessionBase
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.utils.functional import cached_property
from structlog.stdlib import get_logger

from authentik.root.middleware import ClientIPMiddleware

LOGGER = get_logger()


class SessionStore(SessionBase):
    def __init__(self, session_key=None, last_ip=None, last_user_agent=""):
        super().__init__(session_key)
        self._create_kwargs = {
            "last_ip": last_ip or ClientIPMiddleware.default_ip,
            "last_user_agent": last_user_agent,
        }

    @classmethod
    def get_model_class(cls):
        from authentik.core.models import Session

        return Session

    @cached_property
    def model_fields(self):
        return [k.value for k in self.model.Keys]

    def _get_session_from_db(self):
        try:
            return (
                self.model.objects.select_related(
                    "authenticatedsession",
                    "authenticatedsession__user",
                )
                .prefetch_related(
                    "authenticatedsession__user__groups",
                    "authenticatedsession__user__user_permissions",
                )
                .get(
                    session_key=self.session_key,
                    expires__gt=timezone.now(),
                )
            )
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
            self._session_key = None

    async def _aget_session_from_db(self):
        try:
            return (
                await self.model.objects.select_related(
                    "authenticatedsession",
                    "authenticatedsession__user",
                )
                .prefetch_related(
                    "authenticatedsession__user__groups",
                    "authenticatedsession__user__user_permissions",
                )
                .aget(
                    session_key=self.session_key,
                    expires__gt=timezone.now(),
                )
            )
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
            self._session_key = None

    def encode(self, session_dict):
        return pickle.dumps(session_dict, protocol=pickle.HIGHEST_PROTOCOL)

    def decode(self, session_data):
        try:
            return pickle.loads(session_data)  # nosec
        except pickle.PickleError:
            # ValueError, unpickling exceptions. If any of these happen, just return an empty
            # dictionary (an empty session)
            pass
        return {}

    def load(self):
        s = self._get_session_from_db()
        if s:
            return {
                "authenticatedsession": getattr(s, "authenticatedsession", None),
                **{k: getattr(s, k) for k in self.model_fields},
                **self.decode(s.session_data),
            }
        else:
            return {}

    async def aload(self):
        s = await self._aget_session_from_db()
        if s:
            return {
                "authenticatedsession": getattr(s, "authenticatedsession", None),
                **{k: getattr(s, k) for k in self.model_fields},
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
            # Don't save:
            # - unused auth data
            # - related models
            if k in [SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY, "authenticatedsession"]:
                pass
            elif k in self.model_fields:
                args[k] = v
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
            # Don't save:
            # - unused auth data
            # - related models
            if k in [SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY, "authenticatedsession"]:
                pass
            elif k in self.model_fields:
                args[k] = v
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

    def cycle_key(self):
        data = self._session
        key = self.session_key
        self.create()
        self._session_cache = data
        if key:
            self.delete(key)
        if (authenticated_session := data.get("authenticatedsession")) is not None:
            authenticated_session.session_id = self.session_key
            authenticated_session.save(force_insert=True)
