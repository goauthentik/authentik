---
title: CSRF Errors
description: Fix authentik CSRF failures by validating host and origin headers through the admin system info endpoint.
tags:
    - troubleshooting
    - authentication
    - csrf
keywords:
    - authentik csrf
    - host header mismatch
    - origin header error
---

You might see CSRF failures after submitting forms in authentik when a reverse proxy rewrites headers incorrectly.

The fix is to ensure that every request reaches authentik with matching `Host`, `Origin`, and `X-Forwarded-*` headers.

You can diagnose the issue using the following items:

1. Open `https://authentik.company/api/v3/admin/system/` (replace the hostname with your deployment). Search for `HTTP_HOST` and confirm that it matches the public authentik domain and does not include a port unless desired.
2. In the browser, reproduce the action that fails. In the developer tools Network tab, select the POST request and review the **Request Headers**. Verify that `Origin` and `Referer` match the same hostname.
3. If you run authentik behind a proxy that terminates TLS, confirm that the proxy forwards `X-Forwarded-Proto`, `X-Forwarded-Host`, and `X-Forwarded-Port`. Without these headers authentik assumes the request came from the proxy, which causes host mismatches.
