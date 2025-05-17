import socket
from os import environ

IS_CI = "CI" in environ
RETRIES = int(environ.get("RETRIES", "3")) if IS_CI else 1


def get_local_ip() -> str:
    """Get the local machine's IP"""
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)
    return ip_addr
