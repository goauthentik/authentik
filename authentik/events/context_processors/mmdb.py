"""Common logic for reading MMDB files"""

from pathlib import Path

from geoip2.database import Reader
from structlog.stdlib import get_logger

from authentik.events.context_processors.base import EventContextProcessor


class MMDBContextProcessor(EventContextProcessor):
    """Common logic for reading MaxMind DB files, including re-loading if the file has changed"""

    def __init__(self):
        self.reader: Reader | None = None
        self._last_mtime: float = 0.0
        self.logger = get_logger()
        self.load()

    def path(self) -> str | None:
        """Get the path to the MMDB file to load"""
        raise NotImplementedError

    def load(self):
        """Get GeoIP Reader, if configured, otherwise none"""
        path = self.path()
        if path == "" or not path:
            return
        try:
            self.reader = Reader(path)
            self._last_mtime = Path(path).stat().st_mtime
            self.logger.info("Loaded MMDB database", last_write=self._last_mtime, file=path)
        except OSError as exc:
            self.logger.warning("Failed to load MMDB database", path=path, exc=exc)

    def check_expired(self):
        """Check if the modification date of the MMDB database has
        changed, and reload it if so"""
        path = self.path()
        if path == "" or not path:
            return
        try:
            mtime = Path(path).stat().st_mtime
            diff = self._last_mtime < mtime
            if diff > 0:
                self.logger.info("Found new MMDB Database, reopening", diff=diff, path=path)
                self.load()
        except OSError as exc:
            self.logger.warning("Failed to check MMDB age", exc=exc)

    def configured(self) -> bool:
        """Return true if this context processor is configured"""
        return bool(self.reader)
