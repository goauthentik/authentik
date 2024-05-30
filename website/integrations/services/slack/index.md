---
title: Slack
---

<span class="badge badge--secondary">Support level: authentik</span>

## What is Service-Name

> Slack is a platform for collaboration, with chat and real-time video capabilities.
>
> -- https://slack.com

## Preparation

The following placeholders will be used:

-   `slack.company` is the FQDN of the Slack install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik configuration

### Step 1: Log in to authentik

1. Log in to your authentik instance.
2. Click **Admin interface**.

### Step 2: Create a new authentication provider

3. Under **Application**, click **Providers** and create a new provider.
4. Choose **SAML Provider** and then click **Next**.
5. Set the authorization flow to **Authorize Application** (`default-provider-authorization-explicit-consent`).
6. Under **Protocol settings** define the **ACS URL** to `https:_domain-name_.slack.com/sso/saml` and define the **Issuer** as `https://slack.com`.
9. Click **Finish** to create the provider.

### Step 3: Create a new application

10. Create a new application and give it a name.
11. Set the provider to the one you just created.
12. Ensure that the **Policy engine mode** is set to **ANY, any policy must match to grant access**.
13. Click **Create** and then navigate to your [Cloudflare Access dashboard](https://one.dash.cloudflare.com).

## Cloudflare Access configuration

### Step 4: Configure Cloudflare Access

1. Go to the Cloudflare One dashboard.
2. Click **Settings** at the bottom of the menu, then select **Authentication**.

### Step 5: Add a login method
