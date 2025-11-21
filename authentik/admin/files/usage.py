from enum import StrEnum


class FileUsage(StrEnum):
    """Usage types for file storage"""

    MEDIA = "media"
    REPORTS = "reports"


MANAGE_API_USAGES = [FileUsage.MEDIA]
