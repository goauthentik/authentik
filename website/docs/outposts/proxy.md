---
title: Proxy Outpost
---

The proxy outpost sets the following headers:

```
X-Auth-Username: akadmin # The username of the currently logged in user
X-Forwarded-Email: root@localhost # The email address of the currently logged in user
X-Forwarded-Preferred-Username: akadmin  # The username of the currently logged in user
X-Forwarded-User: 900347b8a29876b45ca6f75722635ecfedf0e931c6022e3a29a8aa13fb5516fb # The hashed identifier of the currently logged in user.
```

Additionally, you can set `additionalHeaders` on groups or users to set additional headers.

If you enable *Set HTTP-Basic Authentication* option, the HTTP Authorization header is being set.
