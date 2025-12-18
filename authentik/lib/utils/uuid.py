import uuid


def is_uuid_valid(str: str):
    try:
        uuid.UUID(str)
        return True
    except ValueError:
        return False
