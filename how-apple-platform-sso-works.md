# How Apple Platform SSO works

A reference for understanding the mechanism behind authentik's **tap-to-login Secure Enclave** feature (2026.5). This explains Apple's side; for the authentik setup steps see `tap-to-login-setup-guide.md`.

> **Scope note.** Everything about the *protocol and payload* below is verifiable from Apple's docs and from authentik's `controller.py`. The physical iPhone/Apple Watch tap UX is Apple-internal and handled by the native authentik Agent — there is no authentik source for it. No NFC card reader is involved anywhere in this feature.

---

## Layer 0 — Two things share the name "SSO"

Apple has two nested concepts; conflating them causes most of the confusion:

1. **Extensible SSO** — the general framework (macOS Catalina+ / iOS 13+). An MDM `com.apple.extensiblesso` payload installs a third-party **SSO app extension** that intercepts auth for specific apps/URLs.
2. **Platform SSO (PSSO)** — a **macOS-only superset** (Ventura+) that wires one of those extensions into the **login window, FileVault, and the local account** — not just app traffic. This is what authentik configures.

All Platform SSO is Extensible SSO; not all Extensible SSO is Platform SSO.

## Layer 1 — Extension types (the `Type` field)

| Type | For | Protocols | Flow |
| --- | --- | --- | --- |
| **Redirect** | Modern web auth | OIDC, OAuth 2.0, SAML 2.0 | Sends credentials, then gets data (HTTPS redirect to IdP) |
| **Credential** (challenge/response) | Kerberos-style | Kerberos | Requests data, then gets challenged |

**Platform SSO is always a Redirect-type extension.** authentik hardcodes `"Type": "Redirect"` because it speaks OIDC/OAuth to the authentik IdP. Apple's built-in **Kerberos SSO extension** is the credential-type path and is unrelated to this feature.

## Layer 2 — Registration (two phases)

**① Device registration** — once, silently, at profile install. The Mac proves itself using either a **registration token** (authentik's enrollment token) or **attestation** of genuine Apple hardware. Creates a **shared device key** (Secure Enclave, user-independent) representing the Mac.

**② User registration** — per user, after first login. The IdP provisions a **user key** in the Secure Enclave. This is the credential the user authenticates with afterward.

> **Where tap-to-login fits:** normally the user key is bound to *that Mac's* registration. authentik's 2026.5 `AppleIndependentSecureEnclave` stores a Secure Enclave user key bound to the **authentik user**, not a device registration — so an iPhone/Watch enclave key can satisfy login without being pre-paired to the endpoint.

## Layer 3 — Authentication methods (the `AuthenticationMethod` field)

Classic values (macOS Ventura+):

### `Password`
IdP password is the credential; the local Mac password can be **synced** to it. Supports **WS-Trust** for federated IdPs. No asymmetric key.

### `UserSecureEnclaveKey` ← authentik uses this
The IdP provisions a **P-256 / ES256 key in the Secure Enclave** at user registration. At login the device signs an **embedded JWT assertion** with it; the IdP verifies against the registered public key. **No password crosses the wire.** The private key is generated in and never leaves the Secure Enclave, stored with keychain protection `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`, non-migratory, and shared only with the SSO extension. The **tap on the iPhone/Watch is the user-presence gesture** that authorizes the enclave to sign.

### `SmartCard`
Physical smartcard / **PIV credential** (the NFC-reader world). Also uses an embedded JWT assertion, but the signing key lives **on the card**. authentik does **not** use this method through the agent.

Newer, version-dependent additions (macOS Sequoia / macOS 26 era):

- **Access Key (Apple Wallet)** — an IdP-issued Wallet pass acts as the credential.
- **Web-based authentication** — full IdP web view at the login window, enabling multi-step / MFA flows.

### Common signing mechanism
For Secure Enclave and Smart Card, Apple wraps the proof in an **embedded JWT assertion** signed by the key and incorporating a **nonce** from the IdP (replay protection). The same signed assertion feeds **OIDC, OAuth, SAML 2.0, or Kerberos** on the IdP side.

## Layer 4 — Keys: device vs user

| | Shared device key | User key |
| --- | --- | --- |
| Bound to | The Mac (registration) | The user |
| Created at | Device registration | User registration |
| Purpose | Trusted device channel; gates login-window features | Authenticates the user |

Both are Secure Enclave keys; the distinction is what they represent.

## Layer 5 — Login-window & account modes

Because PSSO hooks the login window and FileVault:

- **Standard** — local account whose password syncs with the IdP.
- **On-demand account creation** — IdP creds / smartcard / web at the login window create a local account on the fly.
- **Authenticated Guest Mode** — short-lived sessions, no local account created.

**Login policies:** *Attempt authentication* (must succeed with IdP if online) vs *Require authentication* (enforced, optional offline grace).

**Token lifecycle:** tokens refresh when missing/expired/>4h old; full re-login every **18h by default** (configurable, 1h min). Tokens live in the keychain, shared only with the extension, non-migratory.

## How authentik maps onto this

From authentik's generated profile (`authentik/endpoints/connectors/agent/controller.py`):

| Payload setting | Meaning |
| --- | --- |
| `PayloadType: com.apple.extensiblesso` + `PlatformSSO{}` | Platform SSO, not just app SSO |
| `Type: Redirect` | OIDC/OAuth redirect extension (not Kerberos) |
| `ExtensionIdentifier: io.goauthentik.platform.psso` | identifies authentik's native agent extension |
| `TeamIdentifier: 232G855Y8N` | authentik's Apple Team ID (shipped by authentik — no Apple Developer account needed on your side) |
| `AuthenticationMethod: UserSecureEnclaveKey` | passwordless enclave-signature method |
| `UseSharedDeviceKeys: True` | uses the device-registration key channel |
| `RegistrationToken` | your enrollment token, consumed at device registration |

The 2026.5 feature adds an enclave **user key bound to the authentik user rather than a device registration** (`AppleIndependentSecureEnclave` in `authentik/endpoints/connectors/agent/models.py`), letting an iPhone/Watch enclave key log in without pre-pairing.

---

## Version caveat

Platform SSO landed in macOS Ventura and grew through Sonoma / Sequoia / macOS 26. The classic `AuthenticationMethod` values are `Password`, `UserSecureEnclaveKey`, `SmartCard`; Wallet/web methods and some login-window features are recent-macOS-dependent. Confirm exact values and features against the macOS version you target.

## Sources

- [Platform Single Sign-on for macOS — Apple Support (Deployment)](https://support.apple.com/guide/deployment/platform-sso-for-macos-dep7bbb05313/web)
- [Single Sign-on security — Apple Platform Security](https://support.apple.com/guide/security/single-sign-on-security-sec0c87ccc6d/web)
- [Extensible Single Sign-on Kerberos payload settings — Apple Support](https://support.apple.com/guide/deployment/extensible-single-sign-kerberos-payload-dep13c5cfdf9/web)
- [Kerberos Single Sign-on extension — Apple Support](https://support.apple.com/guide/deployment/kerberos-sso-extension-depe6a1cda64/web)
- authentik release note: <https://docs.goauthentik.io/releases/2026.5/>
