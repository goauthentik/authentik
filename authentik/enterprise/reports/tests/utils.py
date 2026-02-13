from unittest.mock import MagicMock, patch

patch_license = patch(
    "authentik.enterprise.models.LicenseUsageStatus.is_valid",
    MagicMock(return_value=True),
)
