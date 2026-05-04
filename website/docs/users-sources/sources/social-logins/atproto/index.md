---
title: Log in with AT Protocol
sidebar_label: AT Protocol
tags:
    - source
    - atproto
    - bluesky
    - oauth
---

AT Protocol is the account and data protocol used by Bluesky. A user has a stable decentralized identifier (DID), usually signs in with a handle such as `alice.bsky.social`, and stores account data on a Personal Data Server (PDS).

Use an AT Protocol source when you want users to log in to authentik with a Bluesky or other AT Protocol account. authentik redirects the user to the AT Protocol authorization server, verifies the returned DID, fetches the user's profile, and links the DID to an authentik user.

## What you need

For Bluesky, you do not create an OAuth app in a developer console and you do not get a client secret. You publish a small client metadata JSON document on a public HTTPS URL, and that URL becomes the OAuth `client_id`.

You need:

- A public authentik URL, such as `https://authentik.company`.
- An AT Protocol source slug, such as `atproto`.
- A public HTTPS URL for client metadata, such as `https://metadata.company/authentik-atproto.json`.

## How login works

1. The user clicks the AT Protocol source on the authentik login page.
2. authentik creates a pushed authorization request (PAR) with PKCE and DPoP.
3. The browser is redirected to the AT Protocol authorization server.
4. The user signs in and approves the request.
5. The authorization server redirects back to authentik with a code.
6. authentik exchanges the code using DPoP, receives the user's DID, and verifies that the DID's PDS trusts the issuer.
7. authentik fetches profile data and links the DID to an authentik user.

## Client metadata

Host a JSON document at the exact URL used as `client_id`:

```json
{
    "client_id": "https://metadata.company/authentik-atproto.json",
    "client_name": "authentik",
    "redirect_uris": ["https://authentik.company/source/oauth/callback/atproto/"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "scope": "atproto",
    "token_endpoint_auth_method": "none",
    "application_type": "web",
    "dpop_bound_access_tokens": true
}
```

The callback URL must use the same slug as the authentik source.

To request email from Bluesky, set `scope` to `atproto transition:email` in the metadata and add `transition:email` to the authentik source scopes. Email is optional; authentik can still identify the account by DID and use the AT Protocol handle as the username.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**.
3. Click **New Source**.
4. Select **AT Protocol OAuth Source**.
5. Configure the source:
    - **Name**: a display name, such as `Bluesky`.
    - **Slug**: the slug used in the metadata redirect URI, such as `atproto`.
    - **Consumer Key**: the client metadata URL, for example `https://metadata.company/authentik-atproto.json`.
    - **Consumer Secret**: leave empty. AT Protocol does not use one.
    - **Scopes**: optional extra scopes, such as `transition:email`.
6. Keep the default URL settings for Bluesky, or replace them for another AT Protocol server.
7. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## User matching

By default, authentik maps:

- **Username**: the AT Protocol handle when available, otherwise the DID.
- **Name**: the profile display name when available, otherwise the handle.
- **Email**: the email returned when `transition:email` is granted and supported.

## Troubleshooting

### The source form asks for a consumer secret

AT Protocol sources should not require a consumer secret. Leave it empty.

### Bluesky rejects the client

Check that:

- The client metadata URL is public HTTPS.
- The metadata `client_id` exactly matches the metadata URL.
- The metadata `redirect_uris` value exactly matches `https://authentik.company/source/oauth/callback/atproto/`.
- The authentik source slug matches the callback URL path.
- `token_endpoint_auth_method` is `none`.
- `dpop_bound_access_tokens` is `true`.

## Resources

- [AT Protocol OAuth specification](https://atproto.com/specs/oauth)
