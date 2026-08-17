---
title: Integrate with VMware Cloud Director
sidebar_label: VMware Cloud Director
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is VMware Cloud Director?

> VMware Cloud Director is a platform that enables service providers and enterprises to create multi-tenant virtual data centers (VDCs) from underlying VMware vSphere infrastructure. It supports self-service resource provisioning, secure tenant isolation, and management of compute, storage, and networking via web portals and APIs.
>
> -- https://www.vmware.com/products/cloud-infrastructure/cloud-director

## Preparation

The following placeholders are used in this guide:

- `clouddirector.company` is the FQDN of the VMware Cloud Director instance.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of VMware Cloud Director with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization`:
            - For a provider-level integration, use `https://clouddirector.company/login/oauth?service=provider`.
            - For a tenant-level integration, use `https://clouddirector.company/login/oauth?service=tenant:<organization_name>`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.
4. Open the provider that you created and note the **OpenID Configuration URL** value because it will be required later.

## VMware Cloud Director configuration

1. Log in to VMware Cloud Director with your local administrator account.
2. Navigate to **Administration** > **Identity Providers** > **OIDC**.
3. If you are configuring OIDC for the first time, confirm that the client configuration redirect URI matches the redirect URI that you configured in authentik. For tenant-level configuration, VMware Cloud Director displays the organization-specific URI.
4. Click **Configure**.
5. In the wizard, configure the following values:
    - **Client ID**: enter the Client ID from authentik.
    - **Client Secret**: enter the Client Secret from authentik.
    - **Configuration Discovery**: enable this option.
    - **IDP Well-known Configuration Endpoint**: enter the **OpenID Configuration URL** from the authentik provider.
6. Click **Next**.
7. On the **Endpoint** page, VMware Cloud Director fills the endpoint values from the **IDP Well-known Configuration Endpoint**. Confirm the values, then click **Next**.
8. On the **Scopes** page, keep `openid`, `profile`, and `email`. Add any additional scopes that your environment requires, then click **Next**.
9. On the **Claim Mapping** page, make sure that the user and group claim names match the claims from authentik. The authentik `profile` scope includes a `groups` claim containing the user's authentik group names. Click **Next**.
10. On the **Key Configuration** page, enable **Automatic Key Refresh** if you want VMware Cloud Director to refresh signing keys from authentik automatically. Configure the **Key Refresh Period** and **Key Refresh Strategy** for your environment, then click **Next**.
11. On the **Button Label** page, optionally customize the label that appears on the login page, then click **Save**.

### Map groups to roles

VMware Cloud Director authorizes OIDC users through imported users or groups that are assigned to Cloud Director roles. To use authentik group membership for authorization, import the relevant authentik groups and map each group to a role.

1. Navigate to the group management page:
    - For a provider-level integration, navigate to **Administration** > **Provider Access Control** > **Groups**.
    - For a tenant-level integration, navigate to **Administration** > **Access Control** > **Groups**.
2. Click **Import Groups** and configure the following values:
    - **Source**: select **OIDC**.
    - **Enter the group names**: enter each authentik group name on a separate line.
    - **Assign Role**: select the Cloud Director role to assign to the imported groups.
3. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with VMware Cloud Director, log out of Cloud Director and log back in using **Sign in with OIDC**. If you configured a custom button label, use that button instead.

## Resources

- [VMware Cloud Director documentation - Configure your system to use an OpenID Connect identity provider](https://techdocs.broadcom.com/us/en/vmware-cis/cloud-director/vmware-cloud-director/10-6/configure-your-system-to-use-an-openid-connect-identity-provider.html)
- [VMware Cloud Director documentation - Configure your system to use an OpenID Connect identity provider using your tenant portal](https://techdocs.broadcom.com/us/en/vmware-cis/cloud-director/vmware-cloud-director/10-6/map-for-vmware-cloud-director-tenant-portal-guide-10-6/configuring-identity-providers-using-your-tenant-portal-tenant/configure-your-system-to-use-an-openid-connect-identity-provider-tenant.html)
