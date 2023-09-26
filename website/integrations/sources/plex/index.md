---
title: Plex
---

<span class="badge badge--secondary">Support level: Community</span>

Allows users to authenticate using their Plex credentials

## Preparation

None

## authentik -> Sources

Add _Plex_ as a _source_

-   Name: Choose a name
-   Slug: Set a slug
-   Client ID: Set a unique Client Id or leave the generated ID
-   Press _Load Servers_ to login to plex and pick the authorized Plex Servers for "allowed users"
-   Decide if _anyone_ with a plex account can authenticate or only friends you share with

Save, and you now have Plex as a source.

:::note
For more details on how-to have the new source display on the Login Page see [here](../../../docs/sources/#add-sources-to-default-login-page).
:::
