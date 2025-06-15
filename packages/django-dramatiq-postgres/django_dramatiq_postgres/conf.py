from django.conf import settings


class Conf:
    try:
        conf = settings.DRAMATIQ.copy()
    except AttributeError:
        conf = {}

    encoder_class = conf.get("encoder_class", "dramatiq.encoder.PickleEncoder")

    broker_class = conf.get("broker_class", "django_dramatiq_postgres.broker.PostgresBroker")
    broker_args = conf.get("broker_args", ())
    broker_kwargs = conf.get("broker_kwargs", {})

    middlewares = conf.get(
        "middlewares",
        (
            ("django_dramatiq_postgres.middleware.DbConnectionMiddleware", {}),
            ("dramatiq.middleware.age_limit.AgeLimit", {}),
            ("dramatiq.middleware.time_limit.TimeLimit", {}),
            ("dramatiq.middleware.shutdown.ShutdownNotifications", {}),
            ("dramatiq.middleware.callbacks.Callbacks", {}),
            ("dramatiq.middleware.pipelines.Pipelines", {}),
            ("dramatiq.middleware.retries.Retries", {}),
        ),
    )

    channel_prefix = conf.get("channel_prefix", "dramatiq.tasks")

    task_class = conf.get("task_class", None)

    test = conf.get("test", False)
