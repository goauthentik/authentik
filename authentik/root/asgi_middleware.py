"""ASGI middleware"""

from channels.auth import UserLazyObject
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.sessions import CookieMiddleware
from channels.sessions import InstanceSessionWrapper as UpstreamInstanceSessionWrapper
from channels.sessions import SessionMiddleware as UpstreamSessionMiddleware
from django.contrib.auth.models import AnonymousUser

from authentik.root.middleware import SessionMiddleware as HTTPSessionMiddleware


class InstanceSessionWrapper(UpstreamInstanceSessionWrapper):
    """InstanceSessionWrapper which calls the django middleware to decode
    the session key"""

    async def resolve_session(self):
        raw_session = self.scope["cookies"].get(self.cookie_name)
        session_key = HTTPSessionMiddleware.decode_session_key(raw_session)
        self.scope["session"]._wrapped = await database_sync_to_async(self.session_store)(
            session_key
        )


class SessionMiddleware(UpstreamSessionMiddleware):
    """ASGI SessionMiddleware which uses the modified InstanceSessionWrapper
    wrapper to decode the session key"""

    async def __call__(self, scope, receive, send):
        """
        Instantiate a session wrapper for this scope, resolve the session and
        call the inner application.
        """
        wrapper = InstanceSessionWrapper(scope, send)

        await wrapper.resolve_session()

        return await self.inner(wrapper.scope, receive, wrapper.send)


@database_sync_to_async
def get_user(scope):
    """
    Return the user model instance associated with the given scope.
    If no user is retrieved, return an instance of `AnonymousUser`.
    """
    if "session" not in scope:
        raise ValueError(
            "Cannot find session in scope. You should wrap your consumer in SessionMiddleware."
        )
    user = None
    if (authenticated_session := scope["session"].get("authenticated_session", None)) is not None:
        user = authenticated_session.user
    return user or AnonymousUser()


class AuthMiddleware(BaseMiddleware):
    def populate_scope(self, scope):
        # Make sure we have a session
        if "session" not in scope:
            raise ValueError(
                "AuthMiddleware cannot find session in scope. SessionMiddleware must be above it."
            )
        # Add it to the scope if it's not there already
        if "user" not in scope:
            scope["user"] = UserLazyObject()

    async def resolve_scope(self, scope):
        scope["user"]._wrapped = await get_user(scope)

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        # Scope injection/mutation per this middleware's needs.
        self.populate_scope(scope)
        # Grab the finalized/resolved scope
        await self.resolve_scope(scope)

        return await super().__call__(scope, receive, send)


# Handy shortcut for applying all three layers at once
def AuthMiddlewareStack(inner):
    return CookieMiddleware(SessionMiddleware(AuthMiddleware(inner)))
