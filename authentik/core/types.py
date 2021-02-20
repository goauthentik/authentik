"""authentik core dataclasses"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class UILoginButton:
    """Dataclass for Source's ui_login_button"""

    # Name, ran through i18n
    name: str

    # URL Which Button points to
    url: str

    # Icon URL, used as-is
    icon_url: Optional[str] = None
