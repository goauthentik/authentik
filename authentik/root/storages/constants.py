"""Constants and configuration for storage backends."""

# Storage subdirectories
STORAGE_DIR_APPLICATION_ICONS = "application-icons"
STORAGE_DIR_SOURCE_ICONS = "source-icons"
STORAGE_DIR_FLOW_BACKGROUNDS = "flow-backgrounds"
STORAGE_DIR_PUBLIC = "public"

STORAGE_DIRS = [
    STORAGE_DIR_APPLICATION_ICONS,
    STORAGE_DIR_SOURCE_ICONS,
    STORAGE_DIR_FLOW_BACKGROUNDS,
    STORAGE_DIR_PUBLIC,
]

# Mapping of allowed file extensions to their corresponding MIME types
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

# S3 Configuration keys
S3_CONFIG_KEYS = {
    "session_profile": "storage.media.s3.session_profile",
    "access_key": "storage.media.s3.access_key",
    "secret_key": "storage.media.s3.secret_key",
    "security_token": "storage.media.s3.security_token",
    "bucket_name": "storage.media.s3.bucket_name",
    "region_name": "storage.media.s3.region_name",
    "endpoint_url": "storage.media.s3.endpoint",
    "custom_domain": "storage.media.s3.custom_domain",
} 