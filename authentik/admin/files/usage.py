from enum import StrEnum
from itertools import chain


class FileApiUsage(StrEnum):
    """Usage types for file API"""

    MEDIA = "media"


class FileManagedUsage(StrEnum):
    """Usage types for managed files"""

    REPORTS = "reports"


FileUsage = StrEnum("FileUsage", [(v.name, v.value) for v in chain(FileApiUsage, FileManagedUsage)])
