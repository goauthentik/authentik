"""authentik sessions engine"""

import pickle  # nosec

from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore as SessionBase
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.functional import cached_property
from structlog.stdlib import get_logger

from authentik.root.middleware import ClientIPMiddleware

LOGGER = get_logger()


class SessionStore(SessionBase):
    # Default for `browser_key` distinguishing trusted internal loads (which skip browser
    # binding entirely) from loads on behalf of a browser request, where the middleware
    # always passes the request's browser cookie value (or None if absent).
    UNBOUND = object()

    def __init__(self, session_key=None, last_ip=None, last_user_agent="", browser_key=UNBOUND):
        super().__init__(session_key)
        self._browser_key = browser_key
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

    def _browser_binding_valid(self, session) -> bool:
        """Sessions bound to a browser may only be loaded with that browser's cookie"""
        if self._browser_key is self.UNBOUND:
            return True
        authenticated_session = getattr(session, "authenticatedsession", None)
        if authenticated_session is None or authenticated_session.browser_key is None:
            return True
        return constant_time_compare(authenticated_session.browser_key, self._browser_key or "")

    def _session_queryset(self):
        """Return the session queryset with account-selection relations loaded."""
        return self.model.objects.select_related(
            "authenticatedsession",
            "authenticatedsession__user",
        )

    def _clear_invalid_session(self, exc: Exception) -> None:
        """Clear the active session key after a missing or rejected session load."""
        if isinstance(exc, SuspiciousOperation):
            LOGGER.warning(str(exc))
        self._session_key = None

    def _get_session_from_db(self):
        try:
            session = self._session_queryset().get(
                session_key=self.session_key,
                expires__gt=timezone.now(),
            )
            if not self._browser_binding_valid(session):
                raise SuspiciousOperation("Session denied: browser cookie missing or mismatched")
            return session
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            self._clear_invalid_session(exc)

    async def _aget_session_from_db(self):
        try:
            session = await self._session_queryset().aget(
                session_key=self.session_key,
                expires__gt=timezone.now(),
            )
            if not self._browser_binding_valid(session):
                raise SuspiciousOperation("Session denied: browser cookie missing or mismatched")
            return session
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            self._clear_invalid_session(exc)

    def encode(self, session_dict):
        return pickle.dumps(session_dict, protocol=pickle.HIGHEST_PROTOCOL)

    def decode(self, session_data):
        try:
            return pickle.loads(session_data)  # nosec
        except pickle.PickleError, AttributeError, TypeError:
            # PickleError, ValueError - unpickling exceptions
            # AttributeError - can happen when Django model fields (e.g., FileField) are unpickled
            #                  and their descriptors fail to initialize (e.g., missing storage)
            # TypeError - can happen with incompatible pickled objects
            # If any of these happen, just return an empty dictionary (an empty session)
            LOGGER.warning("Failed to decode session data", exc_info=True)
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
