---
title: WS-Federation Provider
---

The WS-Federation provider is used to integrate with applications and service providers that use [WS-Federation protocol](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adfsod/204de335-ea34-4f9b-ae73-8b7d4c8152d1). WS-Federation is an XML-based identity federation protocol that uses token exchange for federated Single Sign-On (SSO) and IdP authentication, specifically for Windows applications such as SharePoint.

There are similarities between WS-Federation and SAML protocols, but there are several key differences in terminology, most importantly:

- WS-Federation term: **STS (Security Token Service)**
- SAML term: **IdP (Identity Provider)**

:::info SAML2 token support
Note that we only support the SAML2 token type within WS-Federation providers, and that using the WS-Federation provider with Entra ID is not supported because Entra ID requires a SAML 1.0 token.
:::

## Supported URL request parameters

The following URL request parameters are supported in the authentik WS-Federation provider:

- **`wa`**: This is a required parameter that represents the action being requested, typically `wsignin1.0` for signing in. The parameter's value tells the Security Token Service (STS) which operation to execute.
- **`wtrealm`**: The unique identifier (realm) of the Relying Party (RP) or application requesting the security token, for example, urn:my-app:rp. It defines the trust relationship between the RP and the Identity Provider (IdP) and indicates which application is initiating the WS-Federation request. This is a required query parameter that tells the Security Token Service (STS) which relying party the token is intended for.
- **`wreply`**: The target URL to which the Identity Provider (IdP) sends the WS-Federation response containing the security token. This URL is supplied by the Service Provider (SP). authentik verifies that the received `wreply` parameter matches the URL configured by the administrator and stored in the database.
- **`wctx`**: A context value that is used to maintain state between the Relying Party (RP) and the Identity Provider (IdP) across redirects. It serves the same purpose as the `RelayState` parameter in SAML. The RP includes this value in the authentication request, and the IdP returns it unchanged in the response, allowing the RP to validate and restore the original session or request context.

## WS-Federation bindings and endpoints

_Bindings_ define how an Identity Provider (IdP) and the WS-Federation STS (Security Token Service), or IdP in SAML terms, communicate; how messages are transported over network protocols, specifying transport (like HTTP), encoding, and security detail that allow WS-Federation to facilitate secure identity sharing across systems. Both the IdP and STS define various endpoints in their metadata, each associated with a specific WS-Federation binding.

| Endpoint | URL                   |
| -------- | --------------------- |
| SSO/SLO  | `/application/wsfed/` |

## WS-Federation metadata

Using metadata ensures that WS-Federation single sign-on works reliably by exchanging and maintaining identity and connection information. WS-Federation metadata is an XML document that defines how IdPs and SPs securely interact for authentication. It includes information such as endpoints, bindings, certificates, and unique identifiers. The metadata is what you provide the application to configure it for authenticating with authentik.

You can [export WS-Federation metadata](./create-wsfed-provider.md#export-authentik-ws-federation-provider-metadata) from an authentik WS-Federation provider to an STS to automatically provide important endpoint and certificate information to the SP.

## Certificates

The certificates used with WS-Federation to sign Request Security Token Response (RSTR), which contains the assertion, are the same certificates that are used by SAML.

For details, refer to our [SAML certificates documentation](../saml/index.md#certificates).

## WS-Federation property mappings

Property mappings are used during the authentication process to align, or "map", user attributes values between the SP and STS (Security Token Service), the latter being the equivalent of SAML's IdP.

The same property mappings that are used in WS-Federation are used in SAML. For details, refer to our [SAML property mapping documentation](../saml/index.md#certificates).

## Attributes for WS-Federation

WS-Federation and SAML also share the use of the [NameID](../saml/index.md#nameid) and the [AuthnContextClassRef](../saml/index.md#authncontextclassref) attributes.
