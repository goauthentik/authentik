---
title: Integrate with VMware Cloud Director
sidebar_label: VMware Cloud Director
support_level: community
---

## What is Cloud Director

> Deliver secure, efficient, and elastic cloud resources to thousands of enterprises and IT teams worldwide. Operate and manage successful managed public and private cloud service businesses, using VMware Cloud Director.
>
> -- https://www.vmware.com/products/cloud-infrastructure/cloud-director

The following placeholders will be used in the examples below:

- `clouddirector.company` is the FQDN of the Cloud Director instance.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Cloud Director with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://<clouddirector.company>/login/oauth?service=provider`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

:::info Tenant configuration
The redirect URI is for provider level configuration. If you're configuring a tenant-level integration in Cloud Director, use the URI displayed in [step 2. of the Cloud Director configuration](#cloud-director-configuration).
:::

3. Click **Submit** to save the new application and provider.

## Cloud Director configuration

1. Log in to Cloud Director with your local administrator account. Using the menu in the left navigation bar, navigate to **Administration > Identity Providers > OIDC**.

2. Click the blue **Configure** button in the middle of the screen. The wizard opens.

3. In the wizard, enter the following values:
    - Set **Client ID** to the client ID from authentik.
    - Set **Client Secret** to the client secret from authentik.
    - Set **IDP Well-known Configuration Endpoint** to the value of the **OpenID Configuration URL** field in your authentik provider.

4. Click **NEXT**.

5. The values on the **Endpoint** page are fetched automatically from the **IDP Well-known Configuration Endpoint** set before. Example: `https://<authentik.company>/application/o/<slug>/.well-known/openid-configuration` Click **NEXT**.

6. The integration works with the scopes `openid`, `profile` and `email`, which are set by default. If you need other scopes, add them here. Otherwise click **NEXT**.

7. The default Claim Mapping works fine, add any modifications you need and click **NEXT**.

8. On the **Key Configuration** page, you can leave the default key selected, or upload a custom PEM file. Click **NEXT**

9. On the **Button Label** page you are able to customize the label that's shown on the sign in page. Click **SAVE** to save the configuration and close the wizard.

10. It's necessary to link authentik groups to Cloud Director roles, otherwise Cloud Director will deny permissions to authentik users. Using the menu in the left navigation bar, navigate to **Administration > Provider Access Control > Groups**.

:::info Tenant configuration
If you're configuring the integration on a tenant-level in Cloud Director, navigate to **Administration > Access Control > Groups**.
:::

11. Click **IMPORT Groups**. In the dialog fill in the following values:
    - Switch the **Source** dropdown to "OIDC"
    - The dialog now displays a large text area labeled **Enter the group names**. Use a new line for each group.
    - Select the Cloud Director role you wish to map to those authentik groups in the **Assign Role** dropdown.
    - Click **SAVE**.
