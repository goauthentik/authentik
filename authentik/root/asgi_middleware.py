"""ASGI middleware"""
from channels.db import database_sync_to_async
from channels.sessions import InstanceSessionWrapper as UpstreamInstanceSessionWrapper
from channels.sessions import SessionMiddleware as UpstreamSessionMiddleware

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
