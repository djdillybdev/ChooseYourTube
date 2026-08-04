import uuid


def user_uuid(value: uuid.UUID | str) -> uuid.UUID:
    """Normalize authenticated user identifiers at the persistence boundary."""
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(value)
