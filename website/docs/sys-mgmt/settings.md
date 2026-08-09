---
title: System settings
---

System settings control system-wide behavior. They can be changed through the authentik Admin interface or API.

Environment-level and deployment settings are documented in the [configuration options](../install-config/configuration/configuration.mdx).

### Base URL:ak-version[2026.8]

The base URL under which this authentik instance is reachable, for example `https://authentik.company`.

While this setting is empty, authentik displays a warning in the Admin interface until a value is provided. You can seed it at install time with the [`AUTHENTIK_WEB__BASE_URL`](../install-config/configuration/configuration.mdx) configuration option, but the value set here always takes precedence. A trailing slash is removed automatically. Defaults to an empty string.

:::info
Set this to the scheme and host only, without a path. All of authentik is served under [`AUTHENTIK_WEB__PATH`](../install-config/configuration/configuration.mdx#authentik_web__path) (`/` by default), and that prefix is already part of every link authentik generates. So even when you serve authentik under a subpath, for example `AUTHENTIK_WEB__PATH=/authentik/`, the base URL stays `https://authentik.company`, and generated links resolve under `https://authentik.company/authentik/`.
:::

This setting is currently unused until it can be marked as required, starting from authentik version 2026.11.

### Avatars

Configure how authentik should show avatars for users. The following values can be set:

Default: `gravatar,initials`

- `none`: Disables per-user avatars and just shows a 1x1 pixel transparent picture
- `gravatar`: Uses Gravatar with the user's email address
- `initials`: Generated avatars based on the user's name
- Any URL: If you want to use images hosted on another server, you can set any URL.

    Additionally, these placeholders can be used:
    - `%(username)s`: The user's username
    - `%(mail_hash)s`: The email address, md5 hashed
    - `%(upn)s`: The user's UPN, if set (otherwise an empty string)

You can also use an attribute path like `attributes.something.avatar`, which can be used in combination with the file field to allow users to upload custom avatars for themselves.

Multiple modes can be set, and authentik will fall back to the next mode when no avatar could be found. For example, setting this to `gravatar,initials` will attempt to get an avatar from Gravatar, and if the user has not configured one there, it will fall back to a generated avatar.

### Allow users to change name

Enable the ability for users to change their name, defaults to `true`.

### Allow users to change email

Enable the ability for users to change their email address, defaults to `false`.

### Allow users to change username

Enable the ability for users to change their usernames, defaults to `false`.

### Event retention

Configure how long [Events](./events/index.md) are retained for within authentik. Default value is `days=365`. When forwarding events to an external application, this value can be decreased. When changing this value, only new events are affected.

### Reputation: lower limit

Configure a lower limit for [Reputation Policy](../customize/policies/types/reputation.md). Defaults to `-5`.

### Reputation: upper limit

Configure an upper limit for [Reputation Policy](../customize/policies/types/reputation.md). Defaults to `5`.

### Footer links

This option allows you to add linked text (footer links) on the bottom of flow pages. You can also use this setting to display additional static text to the flow pages, even if no URL is provided.

The URL is limited to web and email addresses. If the name is left blank, the URL will be shown.

This is a global setting. All flow pages that are rendered by the [Flow Executor](../add-secure-apps/flows-stages/flow/executors/if-flow.md) will display the footer links.

### GDPR compliance

When enabled, all the events caused by a user will be deleted upon the user's deletion. Defaults to `true`.

### Impersonation

Globally enable/disable impersonation. Defaults to `true`.

### Require reason for impersonation

Require administrators to provide a reason for impersonating a user. Defaults to `true`.

### Default token duration

Default duration for generated tokens. Defaults to `minutes=30`.

### Default token length

Default length of generated tokens. Defaults to 60.
