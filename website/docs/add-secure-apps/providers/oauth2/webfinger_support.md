---
title: WebFinger support
---

## About WebFinger

The WebFinger](https://webfinger.net/) protocol can be used to discover information about people or other entities on the Internet using standard HTTP methods. WebFinger discovers information for a URI that might not be usable as a locator otherwise, such as account or email URIs.

## authentik WebFinger support

Authentik provides a WebFinger endpoint when the **Default application** setting uses an OIDC provider. Instructions on how to set a **Default application** can be found in the [authentik Branding documentation](../../../sys-mgmt/brands.md#external-user-settings)

The WebFinger endpoint is available at: `https://authentik.company/.well-known/webfinger` (where authentik.company is the FQDN of your authentik instance)
