"""Small helper functions"""

import uuid


def get_random_id() -> str:
    """Random hex id"""
    # It is very important that these random IDs NOT start with a number.
    random_id = "_" + uuid.uuid4().hex
    return random_id
