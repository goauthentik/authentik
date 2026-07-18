---
title: Integrate with Cloudflare
sidebar_label: Cloudflare
support_level: community
---

## What is Cloudflare?

> Cloudflare Dashboard is the web interface used to manage Cloudflare accounts, zones, Zero Trust, security, performance, and other Cloudflare services.
>
> -- https://www.cloudflare.com/

## Preparation

The following placeholders are used in this guide:

- `company.com` is the email domain used by users in your Cloudflare organization.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

To proceed, you need:

- A Cloudflare account where you are a **Super Administrator**.
- A Cloudflare Zero Trust organization.
- Control over DNS for `company.com`, because Cloudflare requires a TXT record to verify the email domain before Dashboard SSO can be enabled.
- A working Cloudflare Access identity provider that uses authentik. If this is not already configured, follow the [Cloudflare Access integration guide](../../security/cloudflare-access/index.md) first.

This guide configures SSO for the Cloudflare Dashboard. To protect applications with Cloudflare Access, use the [Cloudflare Access integration guide](../../security/cloudflare-access/index.md) instead.

:::warning Cloudflare Dashboard SSO scope
Cloudflare Dashboard SSO applies to every Cloudflare user with the configured email domain, including users who already exist in Cloudflare. Cloudflare does not support plus-addressed user emails, such as `user+cloudflare@company.com`, with Dashboard SSO.
:::

## authentik configuration

Cloudflare Dashboard SSO uses your existing Cloudflare Access identity provider. Before enabling Dashboard SSO, make sure Cloudflare Access is configured to use authentik and that the identity provider test succeeds in Cloudflare.

To test the identity provider, open the Cloudflare dashboard and navigate to **Zero Trust** > **Integrations** > **Identity providers**. Next to the authentik identity provider, click **Test** and complete the login flow.

## Cloudflare configuration

### Create a recovery API token

Cloudflare recommends creating an Account API token with the `SSO Connector Edit` role before enabling Dashboard SSO. Store this token securely so you can disable Dashboard SSO through the API if an identity provider misconfiguration locks you out.

1. Log in to the Cloudflare dashboard as a Super Administrator.
2. Navigate to **Manage Account** > **Account API Tokens** and click **Create**.
3. Under **Create Custom Token**, click **Get Started**.
4. Add the **Account** permission `SSO Connector Edit`.
5. Click **Continue to Summary**, then click **Create Token**.

### Register the email domain

1. In the Cloudflare dashboard, navigate to **Manage Account** > **Members** > **Settings**.
2. In the Dashboard SSO settings, add a new SSO domain.
3. Enter `company.com` as the email domain, then create the SSO connector.
4. Copy the verification code from Cloudflare.
5. Create a DNS `TXT` record at `company.com` with the verification code as its value. The value must include the `cloudflare_dashboard_sso=` prefix.
6. Wait for Cloudflare to verify domain ownership. If verification times out, begin verification again from the SSO connector actions menu after confirming the DNS record is available.

### Enable Dashboard SSO

1. In the Cloudflare dashboard, navigate to **Manage Account** > **Members** > **Settings**.
2. Open the actions menu for the SSO connector you created.
3. Click **Enable**.

## Configuration verification

To confirm that authentik is properly configured with Cloudflare Dashboard SSO, open Cloudflare Dashboard in a private browser window and sign in with an email address from `company.com`. You should be redirected to authentik, complete the login flow, and return to Cloudflare Dashboard.

## Resources

- [Cloudflare Docs - Set up dashboard SSO](https://developers.cloudflare.com/fundamentals/manage-members/dashboard-sso/)
