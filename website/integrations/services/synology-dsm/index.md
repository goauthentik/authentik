---
title: Integrate with Synology DSM (DiskStation Manager)
sidebar_label: Synology DSM (DiskStation Manager)
---

# Synology DSM (DiskStation Manager)

<span class="badge badge--secondary">Support level: Community</span>

## What is Synology DSM

> Synology Inc. is a Taiwanese corporation that specializes in network-attached storage (NAS) appliances. Synology's line of NAS is known as the DiskStation for desktop models, FlashStation for all-flash models, and RackStation for rack-mount models. Synology's products are distributed worldwide and localized in several languages.
>
> -- https://www.synology.com/en-global/dsm

:::caution
This is tested with DSM 7.1 or newer.
:::

## Preparation

The following placeholders are used in this guide:

- `synology.company` is the FQDN of the Synology DSM server.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

### Step 1

In the Admin interface of authentik, under _Providers_, create an OAuth2/OpenID provider with these settings:

- Name: synology
- Redirect URI: `https://synology.company/#/signin` (Note the absence of the trailing slash, and the inclusion of the webinterface port)
- Signing Key: Select any available key
- Subject mode: Based on the Users's Email (Matching on username could work, but not if you have duplicates due to e.g. a LDAP connection)
- Take note of the 'Client ID' and 'Client secret'

### Step 2

Create an application which uses this provider. Optionally apply access restrictions to the application.

## Synology DSM configuration

To configure Synology DSM to utilize authentik as an OpenID Connect 1.0 Provider:

1. In the DSM Control Panel, navigate to **Domain/LDAP** -> **SSO Client**.
2. Check the **Enable OpenID Connect SSO service** checkbox in the **OpenID Connect SSO Service** section.
3. Configure the following values:

- Profile: OIDC
- Account type: Domain/LDAP/local
- Name: authentik
- Well Known URL: Copy this from the 'OpenID Configuration URL' in the authentik provider (URL ends with '/.well-known/openid-configuration')
- Application ID: The 'Client ID' from the authentik provider
- Application Key: The 'Client secret' from the authentik provider
- Redirect URL: https://synology.company/#/signin (This should match the 'Redirect URI' in authentik exactly)
- Authorization Scope: openid profile email
- Username Claim: preferred_username
- Save the settings.

## Troubleshooting

**Error `not privilege`**

The log in process could fail with a `not privilege` error, when the SSO pop-up is blocked. Allowing pop-ups in the browser configuration resolves this (see https://github.com/authelia/authelia/discussions/6902#discussioncomment-9756400).

## See also:

[Synology DSM SSO Client Documentation](https://kb.synology.com/en-af/DSM/help/DSM/AdminCenter/file_directory_service_sso?version=7)
