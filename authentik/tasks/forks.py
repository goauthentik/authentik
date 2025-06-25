def worker_status():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import WorkerStatusMiddleware

    WorkerStatusMiddleware.worker_status()
