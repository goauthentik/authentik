from typing import Literal, TypedDict

# Based on https://github.com/henribru/google-api-python-client-stubs/blob/master/googleapiclient-stubs/_apis/verifiedaccess/v2/schemas.pyi


class Antivirus(TypedDict, total=False):
    state: Literal["STATE_UNSPECIFIED", "MISSING", "DISABLED", "ENABLED"]


class Challenge(TypedDict, total=False):
    challenge: str


class CrowdStrikeAgent(TypedDict, total=False):
    agentId: str
    customerId: str


class DeviceSignals(TypedDict, total=False):
    allowScreenLock: bool
    antivirus: Antivirus
    browserVersion: str
    builtInDnsClientEnabled: bool
    chromeRemoteDesktopAppBlocked: bool
    crowdStrikeAgent: CrowdStrikeAgent
    deviceAffiliationIds: list[str]
    deviceEnrollmentDomain: str
    deviceManufacturer: str
    deviceModel: str
    diskEncryption: Literal[
        "DISK_ENCRYPTION_UNSPECIFIED",
        "DISK_ENCRYPTION_UNKNOWN",
        "DISK_ENCRYPTION_DISABLED",
        "DISK_ENCRYPTION_ENCRYPTED",
    ]
    displayName: str
    hostname: str
    imei: list[str]
    macAddresses: list[str]
    meid: list[str]
    operatingSystem: Literal[
        "OPERATING_SYSTEM_UNSPECIFIED",
        "CHROME_OS",
        "CHROMIUM_OS",
        "WINDOWS",
        "MAC_OS_X",
        "LINUX",
    ]
    osFirewall: Literal[
        "OS_FIREWALL_UNSPECIFIED",
        "OS_FIREWALL_UNKNOWN",
        "OS_FIREWALL_DISABLED",
        "OS_FIREWALL_ENABLED",
    ]
    osVersion: str
    passwordProtectionWarningTrigger: Literal[
        "PASSWORD_PROTECTION_WARNING_TRIGGER_UNSPECIFIED",
        "POLICY_UNSET",
        "PASSWORD_PROTECTION_OFF",
        "PASSWORD_REUSE",
        "PHISHING_REUSE",
    ]
    profileAffiliationIds: list[str]
    profileEnrollmentDomain: str
    realtimeUrlCheckMode: Literal[
        "REALTIME_URL_CHECK_MODE_UNSPECIFIED",
        "REALTIME_URL_CHECK_MODE_DISABLED",
        "REALTIME_URL_CHECK_MODE_ENABLED_MAIN_FRAME",
    ]
    safeBrowsingProtectionLevel: Literal[
        "SAFE_BROWSING_PROTECTION_LEVEL_UNSPECIFIED", "INACTIVE", "STANDARD", "ENHANCED"
    ]
    screenLockSecured: Literal[
        "SCREEN_LOCK_SECURED_UNSPECIFIED",
        "SCREEN_LOCK_SECURED_UNKNOWN",
        "SCREEN_LOCK_SECURED_DISABLED",
        "SCREEN_LOCK_SECURED_ENABLED",
    ]
    secureBootMode: Literal[
        "SECURE_BOOT_MODE_UNSPECIFIED",
        "SECURE_BOOT_MODE_UNKNOWN",
        "SECURE_BOOT_MODE_DISABLED",
        "SECURE_BOOT_MODE_ENABLED",
    ]
    serialNumber: str
    siteIsolationEnabled: bool
    systemDnsServers: list[str]
    thirdPartyBlockingEnabled: bool
    trigger: Literal["TRIGGER_UNSPECIFIED", "TRIGGER_BROWSER_NAVIGATION", "TRIGGER_LOGIN_SCREEN"]
    windowsMachineDomain: str
    windowsUserDomain: str


class Empty(TypedDict, total=False): ...


class VerifyChallengeResponseRequest(TypedDict, total=False):
    challengeResponse: str
    expectedIdentity: str


class VerifyChallengeResponseResult(TypedDict, total=False):
    attestedDeviceId: str
    customerId: str
    deviceEnrollmentId: str
    devicePermanentId: str
    deviceSignal: str
    deviceSignals: DeviceSignals
    keyTrustLevel: Literal[
        "KEY_TRUST_LEVEL_UNSPECIFIED",
        "CHROME_OS_VERIFIED_MODE",
        "CHROME_OS_DEVELOPER_MODE",
        "CHROME_BROWSER_HW_KEY",
        "CHROME_BROWSER_OS_KEY",
        "CHROME_BROWSER_NO_KEY",
    ]
    profileCustomerId: str
    profileKeyTrustLevel: Literal[
        "KEY_TRUST_LEVEL_UNSPECIFIED",
        "CHROME_OS_VERIFIED_MODE",
        "CHROME_OS_DEVELOPER_MODE",
        "CHROME_BROWSER_HW_KEY",
        "CHROME_BROWSER_OS_KEY",
        "CHROME_BROWSER_NO_KEY",
    ]
    profilePermanentId: str
    signedPublicKeyAndChallenge: str
    virtualDeviceId: str
    virtualProfileId: str
