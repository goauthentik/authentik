"""Help validate and update passwords in LDAP"""
from enum import IntFlag
from re import split
from typing import Optional

from ldap3 import BASE
from ldap3.core.exceptions import LDAPAttributeError, LDAPUnwillingToPerformResult
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.sources.ldap.auth import LDAP_DISTINGUISHED_NAME
from authentik.sources.ldap.models import LDAPSource

LOGGER = get_logger()

NON_ALPHA = r"~!@#$%^&*_-+=`|\(){}[]:;\"'<>,.?/"
RE_DISPLAYNAME_SEPARATORS = r",\.–—_\s#\t"


class PwdProperties(IntFlag):
    """Possible values for the pwdProperties attribute"""

    DOMAIN_PASSWORD_COMPLEX = 1
    DOMAIN_PASSWORD_NO_ANON_CHANGE = 2
    DOMAIN_PASSWORD_NO_CLEAR_CHANGE = 4
    DOMAIN_LOCKOUT_ADMINS = 8
    DOMAIN_PASSWORD_STORE_CLEARTEXT = 16
    DOMAIN_REFUSE_PASSWORD_CHANGE = 32


class PasswordCategories(IntFlag):
    """Password categories as defined by Microsoft, a category can only be counted
    once, hence intflag."""

    NONE = 0
    ALPHA_LOWER = 1
    ALPHA_UPPER = 2
    ALPHA_OTHER = 4
    NUMERIC = 8
    SYMBOL = 16


class LDAPPasswordChanger:
    """Help validate and update passwords in LDAP"""

    _source: LDAPSource

    def __init__(self, source: LDAPSource) -> None:
        self._source = source
        self._connection = source.connection()

    def get_domain_root_dn(self) -> str:
        """Attempt to get root DN via MS specific fields or generic LDAP fields"""
        info = self._connection.server.info
        if "rootDomainNamingContext" in info.other:
            return info.other["rootDomainNamingContext"][0]
        naming_contexts = info.naming_contexts
        naming_contexts.sort(key=len)
        return naming_contexts[0]

    def check_ad_password_complexity_enabled(self) -> bool:
        """Check if DOMAIN_PASSWORD_COMPLEX is enabled"""
        root_dn = self.get_domain_root_dn()
        try:
            root_attrs = self._connection.extend.standard.paged_search(
                search_base=root_dn,
                search_filter="(objectClass=*)",
                search_scope=BASE,
                attributes=["pwdProperties"],
            )
            root_attrs = list(root_attrs)[0]
        except (LDAPAttributeError, LDAPUnwillingToPerformResult, KeyError, IndexError):
            return False
        raw_pwd_properties = root_attrs.get("attributes", {}).get("pwdProperties", None)
        if not raw_pwd_properties:
            return False

        try:
            pwd_properties = PwdProperties(raw_pwd_properties)
        except ValueError:
            return False
        if PwdProperties.DOMAIN_PASSWORD_COMPLEX in pwd_properties:
            return True

        return False

    def change_password(self, user: User, password: str):
        """Change user's password"""
        user_dn = user.attributes.get(LDAP_DISTINGUISHED_NAME, None)
        if not user_dn:
            LOGGER.info(f"User has no {LDAP_DISTINGUISHED_NAME} set.")
            return
        try:
            self._connection.extend.microsoft.modify_password(user_dn, password)
        except (LDAPAttributeError, LDAPUnwillingToPerformResult):
            self._connection.extend.standard.modify_password(user_dn, new_password=password)

    def _ad_check_password_existing(self, password: str, user_dn: str) -> bool:
        """Check if a password contains sAMAccount or displayName"""
        users = list(
            self._connection.extend.standard.paged_search(
                search_base=user_dn,
                search_filter=self._source.user_object_filter,
                search_scope=BASE,
                attributes=["displayName", "sAMAccountName"],
            )
        )
        if len(users) != 1:
            raise AssertionError()
        user_attributes = users[0]["attributes"]
        # If sAMAccountName is longer than 3 chars, check if its contained in password
        if len(user_attributes["sAMAccountName"]) >= 3:
            if password.lower() in user_attributes["sAMAccountName"].lower():
                return False
        # No display name set, can't check any further
        if len(user_attributes["displayName"]) < 1:
            return True
        for display_name in user_attributes["displayName"]:
            display_name_tokens = split(RE_DISPLAYNAME_SEPARATORS, display_name)
            for token in display_name_tokens:
                # Ignore tokens under 3 chars
                if len(token) < 3:
                    continue
                if token.lower() in password.lower():
                    return False
        return True

    def ad_password_complexity(self, password: str, user: Optional[User] = None) -> bool:
        """Check if password matches Active directory password policies

        https://docs.microsoft.com/en-us/windows/security/threat-protection/
            security-policy-settings/password-must-meet-complexity-requirements
        """
        if user:
            # Check if password contains sAMAccountName or displayNames
            if LDAP_DISTINGUISHED_NAME in user.attributes:
                existing_user_check = self._ad_check_password_existing(
                    password, user.attributes.get(LDAP_DISTINGUISHED_NAME)
                )
                if not existing_user_check:
                    LOGGER.debug("Password failed name check", user=user)
                    return existing_user_check

        # Step 2, match at least 3 of 5 categories
        matched_categories = PasswordCategories.NONE
        required = 3
        for letter in password:
            # Only match one category per letter,
            if letter.islower():
                matched_categories |= PasswordCategories.ALPHA_LOWER
            elif letter.isupper():
                matched_categories |= PasswordCategories.ALPHA_UPPER
            elif not letter.isascii() and letter.isalpha():
                # Not exactly matching microsoft's policy, but count it as "Other unicode" char
                # when its alpha and not ascii
                matched_categories |= PasswordCategories.ALPHA_OTHER
            elif letter.isnumeric():
                matched_categories |= PasswordCategories.NUMERIC
            elif letter in NON_ALPHA:
                matched_categories |= PasswordCategories.SYMBOL
        if bin(matched_categories).count("1") < required:
            LOGGER.debug(
                "Password didn't match enough categories",
                has=matched_categories,
                must=required,
            )
            return False
        LOGGER.debug("Password matched categories", has=matched_categories, must=required)
        return True
