from __future__ import absolute_import

from sentry.auth import register

from .provider import PassbookOAuth2Provider

register('passbook', PassbookOAuth2Provider)
