"""passbook core dataclasses"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class UIUserSettings:
    """Dataclass for Factor and Source's user_settings"""

    name: str
    icon: str
    view_name: str


@dataclass
class UILoginButton:
    """Dataclass for Source's ui_ui_login_button"""

    # Name, ran through i18n
    name: str

    # URL Which Button points to
    url: str

    # Icon name, ran through django's static
    icon_path: Optional[str] = None

    # Icon URL, used as-is
    icon_url: Optional[str] = None
