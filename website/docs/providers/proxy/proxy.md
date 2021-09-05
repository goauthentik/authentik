---
title: Proxy provider
---

The proxy outpost sets the following headers:

```
X-Auth-Username: akadmin # The username of the currently logged in user
X-Auth-Groups: foo|bar|baz # The groups the user is member of, separated by a pipe
X-Forwarded-Email: root@localhost # The email address of the currently logged in user
X-Forwarded-Preferred-Username: akadmin  # The username of the currently logged in user
X-Forwarded-User: 900347b8a29876b45ca6f75722635ecfedf0e931c6022e3a29a8aa13fb5516fb # The hashed identifier of the currently logged in user.
```

Additionally, you can set `additionalHeaders` on groups or users to set additional headers.

If you enable *Set HTTP-Basic Authentication* option, the HTTP Authorization header is being set.

# HTTPS

The outpost listens on both 4180 for HTTP and 4443 for HTTPS.

:::info
If your upstream host is HTTPS, and you're not using forward auth, you need to access the outpost over HTTPS too.
:::

# Logging out

Login is done automatically when you visit the domain without a valid cookie.

When using single-application mode, navigate to `app.domain.tld/akprox/sign_out`.

When using domain-level mode, navigate to `auth.domain.tld/akprox/sign_out`, where auth.domain.tld is the external host configured for the provider.

To log out, navigate to `/akprox/sign_out`.
