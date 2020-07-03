"""passbook oidc claim helpers"""
from typing import Any, Dict

from passbook.core.models import User


def userinfo(claims: Dict[str, Any], user: User) -> Dict[str, Any]:
    """Populate claims from userdata"""
    claims["name"] = user.name
    claims["given_name"] = user.name
    claims["family_name"] = user.name
    claims["email"] = user.email
    claims["preferred_username"] = user.username
    return claims
