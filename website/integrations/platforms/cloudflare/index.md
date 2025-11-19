---
title: Integrate with Cloudflare
sidebar_label: Cloudflare
support_level: community
---

## What is Cloudflare

> Cloudflare is a global cloud services provider that enhances the security, performance, and reliability of websites and applications through its content delivery network (CDN), DDoS protection, and web infrastructure solutions.
>
> -- https://www.cloudflare.com/

## Preparation

The following placeholders are used in this guide:

- `acmecorp.company` is the FQDN of your company's email domain.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning Prerequisites
Before proceeding, ensure you have a Cloudflare account and that authentik is already configured with Cloudflare Access, following the steps in our [integration guide](../../security/cloudflare-access/index.md).
:::

## Cloudflare configuration

1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com) as an administrator.
2. Navigate to **My account** (sidebar) > **Account API tokens** and click **Create**.
3. Under **Create Custom Token**, select **Get Started**. Add an `Account` permission with the `SSO Connector: Edit` scope. Store this token securely; you will need it throughout this guide, and it can also be used to disable SSO if you are locked out. Complete the process by selecting **Continue to Summary**, then **Create Token**.
4. Copy your Cloudflare Account ID from the dashboard URL. For example, in `https://dash.cloudflare.com/<account_id>/home/domains`, the `<account_id>` value is what you need.
5. Export the following environment variables in your terminal:

```sh
export CLOUDFLARE_API_TOKEN=<your_api_token>
export CLOUDFLARE_ACCOUNT_ID=<your_account_id>
```

5. Create the SSO connector with the following command:

```sh
curl "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/sso_connectors" \
  --request POST \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"email_domain":"acmecorp.company"}'
```

An example of a successful response:

```json
{
    "result": {
        "id": "<your_sso_connector_id>",
        "enabled": false,
        "email_domain": "acmecorp.company",
        "created_on": "2025-09-25T21:05:20.462622Z",
        "updated_on": "2025-09-25T21:05:20.462622Z",
        "verification": {
            "code": "cloudflare_dashboard_sso=11111111111111111111",
            "status": "pending"
        }
    },
    "success": true,
    "errors": [],
    "messages": []
}
```

6. Copy the `code` value and create a DNS TXT record containing it at the apex of your email domain.

7. Next, export your connector ID:

```sh
export CLOUDFLARE_SSO_CONNECTOR_ID=<your_sso_connector_id>
```

8. After the DNS record has propagated, enable the connector with the following command:

```sh
curl "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/sso_connectors/$CLOUDFLARE_SSO_CONNECTOR_ID" \
  --request PATCH \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"enabled": true}'
```

## Configuration verification

To verify the integration, log in to your company’s Cloudflare Access installation with authentik. A new application named **SSO App** should appear in the dashboard. Selecting it should redirect you to the Cloudflare Dashboard.

## Resources

- [Cloudflare Dashboard SSO Documentation](https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/dash-sso-apps/)
