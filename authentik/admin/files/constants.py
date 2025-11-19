# File upload limits
MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024  # 3MB
MAX_FILE_PATH_LENGTH = 1024
MAX_PATH_COMPONENT_LENGTH = 255

# Allowed MIME types per usage
ALLOWED_MIME_TYPES = {
    "media": ["image/"],
    "reports": None,
}
