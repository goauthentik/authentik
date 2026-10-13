from django.db import connection


def make_key(key: str, key_prefix: str, version: int) -> str:
    return f"{connection.schema_name}:{key_prefix}:{version}:{key}"


def reverse_key(key: str) -> str:
    return key.split(":", 3)[3]
