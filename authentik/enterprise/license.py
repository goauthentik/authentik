"""License utils"""


from dataclasses import dataclass
from datetime import datetime


@dataclass
class LicenseStatus:
    is_licensed: bool
    license_expiry: datetime
