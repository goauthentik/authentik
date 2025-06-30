- `ak_logger`: structlog BoundLogger. See ([structlog documentation](https://www.structlog.org/en/stable/api.html#structlog.BoundLogger))

    Example:

    ```python
    ak_logger.debug("This is a test message")
    ak_logger.warning("This will be logged with a warning level")
    ak_logger.info("Passing structured data", request=request)
    ```

- `requests`: requests Session object. See ([request documentation](https://requests.readthedocs.io/en/master/user/advanced/))
