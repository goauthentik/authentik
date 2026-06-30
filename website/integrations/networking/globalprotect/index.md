---
title: Integrate with GlobalProtect
sidebar_label: GlobalProtect
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is GlobalProtect?

> GlobalProtect simplifies remote access management with identity-aware authentication and client or clientless deployment methods for mobile users.
>
> -- https://www.paloaltonetworks.com/sase/globalprotect

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `gp.company` is the FQDN of the GlobalProtect portal or gateway that uses this provider.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::caution Portal certificate
A trusted web certificate must be bound to the GlobalProtect portal. The certificate can be signed by a trusted internal root certificate authority (CA), but a self-signed, expired, or otherwise invalid portal certificate can cause SAML authentication to fail.
:::

### Prerequisites

- A working GlobalProtect portal and gateway configuration.
- A certificate configured in authentik for signing SAML responses.
- Administrative access to the Palo Alto Networks firewall or Panorama instance that manages GlobalProtect.

## authentik configuration

To support the integration of GlobalProtect with authentik, you need to create an application/provider pair in authentik.

If multiple GlobalProtect portals or gateways initiate SAML requests with different FQDNs, create a separate application/provider pair for each FQDN. Each provider must use the matching FQDN in the **ACS URL** and **Audience**.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://gp.company:443/SAML20/SP/ACS`.
        - Set the **Audience** to `https://gp.company:443/SAML20/SP`.
        - Under **Advanced protocol settings**, select an available **Signing Certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage access to the application.
3. Click **Submit** to save the new application and provider.

:::info Non-standard SAML ports
If GlobalProtect uses a non-standard SAML port, replace `:443` in the **ACS URL** and **Audience** with the configured SAML port. Configure the same custom SAML port on the firewall.
:::

### Download the SAML metadata

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and open the GlobalProtect provider.
3. Under **Metadata**, click **Download**. The metadata file is required in the GlobalProtect configuration.

## GlobalProtect configuration

### Create a SAML identity provider profile

1. Log in to the Palo Alto Networks firewall or Panorama instance that manages GlobalProtect.
2. Navigate to **Device** > **Server Profiles** > **SAML Identity Provider**.
3. Click **Import** and configure the profile:
    - **Profile Name**: provide a descriptive name, such as `authentik`.
    - **Identity Provider Metadata**: upload the metadata file you downloaded from authentik.
    - **Validate Identity Provider Certificate**: enable this if you have configured a certificate profile that trusts the CA which issued the authentik signing certificate.
4. Click **OK**.

### Create an authentication profile

1. Navigate to **Device** > **Authentication Profile** and click **Add**.
2. Configure the profile:
    - **Name**: provide a descriptive name.
    - **Type**: select **SAML**.
    - **IdP Server Profile**: select the SAML identity provider profile you created.
    - **Certificate for Signing Requests**: select a certificate only if authentik is configured to validate signed SAML requests.
    - **Certificate Profile**: select a certificate profile if you enabled **Validate Identity Provider Certificate** in the SAML identity provider profile.
    - **Username Attribute**: `http://schemas.goauthentik.io/2021/02/saml/username`
3. Open the **Advanced** tab and add `all` to **Allow List**.
4. Click **OK**.

### Assign the authentication profile

1. Navigate to **Network** > **GlobalProtect** > **Portals** and open the portal that should use SAML.
2. Open the portal authentication settings and select the authentication profile you created.
3. If you do not require a client certificate, select **Yes (User Credentials OR Client Certificate Required)**.
4. Navigate to **Network** > **GlobalProtect** > **Gateways** and make the same authentication profile change for each gateway that should use SAML. If a gateway uses a different FQDN in its SAML request, use an authentication profile connected to a matching authentik provider.
5. Commit the changes.

## Configuration verification

To confirm that authentik is properly configured with GlobalProtect, open the GlobalProtect app or the GlobalProtect portal, connect to `gp.company`, and complete the authentik sign-in flow. After authentication, GlobalProtect should return to the portal or gateway and complete the connection.

## Resources

- [Palo Alto Networks - Set Up SAML Authentication](https://docs.paloaltonetworks.com/globalprotect/administration/globalprotect-user-authentication/set-up-external-authentication/set-up-saml-authentication)
- [Palo Alto Networks - Configure Mobile Users without Cloud Identity Engine](https://docs.paloaltonetworks.com/prisma-access/integration/microsoft-integrations-with-prisma-access/azure-ad-saml-authentication-for-mobile-user-deployments/configure-mobile-users-without-cloud-identity-engine)
- [Palo Alto Networks - SAML Authentication for GlobalProtect Portals on Non-Standard Ports](https://docs.paloaltonetworks.com/globalprotect/administration/globalprotect-user-authentication/set-up-external-authentication/set-up-saml-authentication/saml-authentication-for-globalprotect-portals-on-non-standard-ports)
