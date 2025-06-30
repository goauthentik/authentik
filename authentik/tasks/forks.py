def worker_status():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import WorkerStatusMiddleware

    WorkerStatusMiddleware.worker_status()


def worker_metrics():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import MetricsMiddleware

    MetricsMiddleware.run()
