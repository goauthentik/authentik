---
title: API
---

Our API reference documentation is generated, and is included [here](../api/reference/authentik.info.mdx) in our regular documentation Table of Contents, under **API -> Reference**.

You can also access your installation's own, instance-specific API Browser. Starting with 2021.3.5, every authentik instance has a built-in API browser, which can be accessed at <code>https://<em>authentik.company</em>/api/v3/</code>.

To generate an API client you can use the OpenAPI v3 schema at <code>https://<em>authentik.company</em>/api/v3/schema/</code>.

While testing, the API requests are authenticated by your browser session.

## Authentication

For any of the token-based methods, set the `Authorization` header to `Bearer <token>`.

### Session

When authenticating with a flow, you'll get an authenticated Session cookie, that can be used for authentication. Keep in mind that in this context, a CSRF header is also required.

### API Token

Users can create tokens to authenticate as any user with a static key, which can optionally be expiring and auto-rotate.

### JWT Token

OAuth2 clients can request the scope `goauthentik.io/api`, which allows their OAuth Access token to be used to authenticate to the API.
