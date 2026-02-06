---
title: WS-Fed Provider
---

The WS-Fed provider is used to integrate with applications and service providers that use [WS-Fed protocol](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adfsod/204de335-ea34-4f9b-ae73-8b7d4c8152d1). (WS-Fed) is an XML-based identity federation protocol that uses token exchange for federated Single Sign-On (SSO) and IdP authentication, specifically for Windows applications such as Sharepoint.

There are similarities between WS-Fed and SAML protocols, but there are also key differences. Some to be aware of include:

| WS-Fed                                                                                                               | SAML                                         |
| -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Request Security Token (RST) acts as the secure token sent by the Identity Provider (IdP) to the Relying Party (SP). | SAML request                                 |
| Request Security Token Response (RSTR)                                                                               | SAML response with an assertion              |
| RP (relying party) and STS (Security Token Service)                                                                  | RP (relying party) and SP (Service Provider) |

- WS-Fed uses a _Request Security Token (RST)_ whereas SAML uses a _SAML request_.
- With WS-Fed, the identity provider returns a Request Security Token Response (RSTR), whereas SAML returns a SAML response that contains an assertion.
- ?
- ?

## Supported URL request parameters

... only one shows in UI (the reply one) `wa`, `wtrealm` (a trust realm, which instance of what app is talking to it), `wreply`, simpilar to reply URL, this is the url the SP gives us.. authentik compares this to the one that the Admin who created the provider gave and is now in DB), and `wctxt` which is same as “relay state” in SAML. We give this back and they validate that it is same.

- **wa**: The action being requested, typically wsignin1.0 for sign-in.
- **wtrealm**: The identifier (realm) of the Relying Party (RP) or application receiving the token, e.g., urn:my-app:rp.
- **wreply**: The URL where the identity provider should send the response (security token).
- **wctx**: A context value to be passed back and forth, allowing the RP to maintain state across redirects.

## WS-Fed bindings and endpoints

_Bindings_ define how an Identity Provider (IdP) and a Service Provider (SP) communicate; how messages are transported over network protocols, specifying transport (like HTTP), encoding, and security detail that allow WS-Fed to facilitate secure identity sharing across systems. Both IdPs and SPs define various endpoints in their metadata, each associated with a specific WS-Fed binding.

In authentik, you can select one of two WS-Fed bindings: `HTTP Redirect` or `HTTP POST`.

_Endpoint URLs_ specify where and how the messages are sent according to that binding. The table below shows the supported endpoints for each binding:

| Endpoint | URL |
| ------------------------- | ------------------------------------------------------------ | |
| SSO (POST binding) | `/application/ws-fed/<application_slug>/sso/binding/post/` |
| SSO (IdP-initiated login) | `/application/ws-fed/<application_slug>/sso/binding/init/` |
| SLO (POST binding) | `/application/ws-fed/<application_slug>/slo/binding/post/` |
| Metadata Download | `/application/ws-fed/<application_slug>/metadata/` |

## WS-Fed metadata

Using metadata ensures that WS-Fed single sign-on works reliably by exchanging and maintaining identity and connection information. WS-Fed metadata is an XML document that defines how IdPs and SPs securely interact for authentication. It includes information such as endpoints, bindings, certificates, and unique identifiers. The metadata is what you provide the application (the STS, in WS-Fed terms) in order to configure it for authenticating with authentik.

### Importing SP WS-Fed metadata

You can import WS-Fed metadata to automatically configure a WS-Fed provider based on the requirements of an STS.

### Exporting authentik WS-Fed metadata

You can export WS-Fed metadata from an authentik WS-Fed provider to an STS to automatically provide important endpoint and certificate information to the SP.

+++
Reply URL: Enter the Application Callback URL (the applications's Assertion Consumer Service URL) where the token should be sent.

## Certificates

The certificates used with WS-Fed to sign Request Security Token Response (RSTR), which contains the assertion, are the same certificates that are used by SAML.

For details, refer to our [SAML provider documentation](../saml/index.md#certificates).

## Ws_Fed property mappings
