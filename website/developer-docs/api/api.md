---
title: API
---

Starting with 2021.3.5, every authentik instance has a built-in API browser, which can be accessed at https://authentik.company/api/v3/.

To generate an API client, you can use the OpenAPI v3 schema at https://authentik.company/api/v3/schema/.

While testing, the API requests are authenticated by your browser session.

## Authentication

For any of the token-based methods, set the `Authorization` header to `Bearer <token>`.

### Session

When authenticating with a flow, you'll get an authenticated Session cookie, that can be used for authentication. Keep in mind that in this context, a CSRF header is also required.

### API Token

Users can create tokens to authenticate as any user with a static key, which can optionally be expiring and auto-rotate.

### JWT Token

OAuth2 clients can request the scope `goauthentik.io/api`, which allows their OAuth Access token to be used to authenticate to the API.
