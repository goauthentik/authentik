---
title: System Settings
---

These settings are similar to the configuration options listed [here](../install-config/configuration/configuration.mdx), however they can only be adjusted through the authentik Admin interface or API.

### Avatars

Configure how authentik should show avatars for users. Following values can be set:

Default: `gravatar,initials`

- `none`: Disables per-user avatars and just shows a 1x1 pixel transparent picture
- `gravatar`: Uses gravatar with the user's email address
- `initials`: Generated avatars based on the user's name
- Any URL: If you want to use images hosted on another server, you can set any URL.

    Additionally, these placeholders can be used:

    - `%(username)s`: The user's username
    - `%(mail_hash)s`: The email address, md5 hashed
    - `%(upn)s`: The user's UPN, if set (otherwise an empty string)

You can also use an attribute path like `attributes.something.avatar`, which can be used in combination with the file field to allow users to upload custom avatars for themselves.

Multiple modes can be set, and authentik will fallback to the next mode when no avatar could be found. For example, setting this to `gravatar,initials` will attempt to get an avatar from Gravatar, and if the user has not configured on there, it will fallback to a generated avatar.

### Allow users to change name

Enable the ability for users to change their name, defaults to `true`.

### Allow users to change email

Enable the ability for users to change their Email address, defaults to `false`.

### Allow users to change username

Enable the ability for users to change their usernames, defaults to `false`.

### Event retention

Configure how long [Events](./events/index.md) are retained for within authentik. Default value is `days=365`. When forwarding events to an external application, this value can be decreased. When changing this value, only new events are affected.

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
