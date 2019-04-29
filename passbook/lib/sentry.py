"""passbook sentry integration"""


def before_send(event, hint):
    """Check if error is database error, and ignore if so"""
    from django.core.exceptions import OperationalError
    from django_redis.exceptions import ConnectionInterrupted

    ignored_classes = [
        OperationalError,
        ConnectionInterrupted,
    ]
    if 'exc_info' in hint:
        _exc_type, exc_value, _ = hint['exc_info']
        if isinstance(exc_value, ignored_classes):
            return None
    return event
