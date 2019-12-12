# Providers

Providers allow external Applications to authenticate against passbook and use its User Information.

## OpenID Provider

This provider uses the commonly used OpenID Connect variation of OAuth2.

## OAuth2 Provider

This provider is slightly different than the OpenID Provider. While it uses the same basic OAuth2 Protocol, it provides a GitHub-compatible Endpoint. This allows you to integrate Applications, which don't support Custom OpenID Providers.
The API exposes Username, E-Mail, Name and Groups in a GitHub-compatible format.

## SAML Provider

This provider allows you to integrate Enterprise Software using the SAML2 Protocol. It supports signed Requests. This Provider also has [Property Mappings](property-mappings.md#saml-property-mapping), which allows you to expose Vendor-specific Fields.
