---
title: Generic OAuth Source
---

## Generic OAuth Source

:::note
All Integration-specific Sources are documented in the Integrations Section
:::

This source allows users to enroll themselves with an external OAuth-based Identity Provider. The generic provider expects the endpoint to return OpenID-Connect compatible information. Vendor-specific implementations have their own OAuth Source.

-   Policies: Allow/Forbid users from linking their accounts with this provider.
-   Request Token URL: This field is used for OAuth v1 implementations and will be provided by the provider.
-   Authorization URL: This value will be provided by the provider.
-   Access Token URL: This value will be provided by the provider.
-   Profile URL: This URL is called by authentik to retrieve user information upon successful authentication.
-   Consumer key/Consumer secret: These values will be provided by the provider.

### OpenID Connect

:::info
Requires authentik 2022.6
:::

#### Well-known

Instead of configuring the URLs for a source manually, and the application you're configuring implements the [OpenID Connect Discovery Spec](https://openid.net/specs/openid-connect-discovery-1_0.html), you can configure the source with a single URL. The URL should always end with `.well-known/openid-configuration`. Many applications don't explicitly mention this URL, but for most of them it will be `https://application.company/.well-known/openid-configuration`.

This URL is fetched upon saving the source, and all the URLs will be replaced by the ones from the Discovery document. No automatic re-fetching is done.

#### JWKS

To simplify Machine-to-machine authentication, you can create an OAuth Source as "trusted" source of JWTs. Create a source and configure either the Well-known URL or the OIDC JWKS URL, or you can manually enter the JWKS data if you so desire.

Afterwards, this source can be selected in one or multiple OAuth2 providers, and any JWT issued by any of the configured sources' JWKS will be able to authenticate. To learn more about this, see [JWT-authentication](/docs/providers/oauth2/client_credentials#jwt-authentication).
