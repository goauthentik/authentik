"""Constants."""

from pathlib import Path

# File upload limits
MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024  # 3MB
MAX_FILE_PATH_LENGTH = 1024
MAX_PATH_COMPONENT_LENGTH = 255

# Allowed MIME types per usage
ALLOWED_MIME_TYPES = {
    "media": ["image/"],
    "reports": None,
}

# Static file paths
STATIC_SOURCES_DIR = Path("web/authentik/sources")
STATIC_ASSETS_DIRS = ["assets/icons", "assets/images"]
STATIC_DIST_PREFIX = "web/dist"

# Allowed file extensions for static files
STATIC_FILE_EXTENSIONS = [".svg", ".png", ".jpg", ".jpeg"]

# S3 configuration defaults
S3_PRESIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour
S3_DEFAULT_ACL = "private"

# URL schemes
EXTERNAL_URL_SCHEMES = ["http:", "https://"]
FONT_AWESOME_SCHEME = "fa://"
STATIC_PATH_PREFIX = "/static"
