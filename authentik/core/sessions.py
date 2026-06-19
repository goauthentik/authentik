"""authentik sessions engine"""

import pickle  # nosec
from typing import TYPE_CHECKING

from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore as SessionBase
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest
from django.utils import timezone
from django.utils.functional import cached_property
from structlog.stdlib import get_logger

from authentik.root.middleware import ClientIPMiddleware

if TYPE_CHECKING:
    from authentik.core.models import AuthenticatedSession, User

LOGGER = get_logger()


def authenticated_session_from_request(
    request: HttpRequest, user: User
) -> AuthenticatedSession | None:
    """Create a new authenticated session from an HTTP request."""
    from authentik.core.models import AuthenticatedSession, Session

    if not hasattr(request, "session") or not request.session.exists(request.session.session_key):
        return None
    session = Session.objects.filter(session_key=request.session.session_key).first()
    if session is None:
        return None
    authenticated_session, _ = AuthenticatedSession.objects.update_or_create(
        session=session,
        defaults={
            "user": user,
            "is_current": True,
        },
    )
    return bind_authenticated_session_to_browser(request, authenticated_session)


def bind_authenticated_session_to_browser(
    request: HttpRequest, authenticated_session: AuthenticatedSession
) -> AuthenticatedSession:
    """Bind an authenticated session to the request's browser key."""
    from authentik.core.models import AuthenticatedSession
    from authentik.root.middleware import SessionMiddleware

    browser_key = SessionMiddleware.ensure_browser_key(request)
    if browser_key:
        # The new login takes over the browser; older logins become switch targets.
        AuthenticatedSession.objects.filter(browser_key=browser_key).exclude(
            session=authenticated_session.session
        ).update(is_current=False)
        if authenticated_session.browser_key != browser_key or not authenticated_session.is_current:
            authenticated_session.browser_key = browser_key
            authenticated_session.is_current = True
            authenticated_session.save(update_fields=["browser_key", "is_current"])
    return authenticated_session


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

    @staticmethod
    def _check_superseded(session) -> None:
        """Reject browser logins superseded by a newer login."""
        authenticated_session = getattr(session, "authenticatedsession", None)
        if (
            authenticated_session is not None
            and authenticated_session.browser_key
            and not authenticated_session.is_current
        ):
            raise SuspiciousOperation("Session denied: superseded by a newer login")

    def _get_session_from_db(self):
        try:
            session = self.model.objects.select_related(
                "authenticatedsession",
                "authenticatedsession__user",
            ).get(
                session_key=self.session_key,
                expires__gt=timezone.now(),
            )
            self._check_superseded(session)
            return session
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
            self._session_key = None

    async def _aget_session_from_db(self):
        try:
            session = await self.model.objects.select_related(
                "authenticatedsession",
                "authenticatedsession__user",
            ).aget(
                session_key=self.session_key,
                expires__gt=timezone.now(),
            )
            self._check_superseded(session)
            return session
        except (self.model.DoesNotExist, SuspiciousOperation) as exc:
            if isinstance(exc, SuspiciousOperation):
                LOGGER.warning(str(exc))
            self._session_key = None

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
