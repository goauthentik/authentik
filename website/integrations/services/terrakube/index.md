---
title: Integrate with Terrakube
sidebar_label: Terrakube
support_level: community
---

## What is Terrakube

> Terrakube is an open-source collaboration platform designed for managing remote Infrastructure-as-Code (IaC) operations with Terraform. It serves as a alternative to proprietary tools like Terraform Enterprise.
>
> -- https://terrakube.io/

## Preparation

The following placeholders are used in this guide:

- `terrakube-dex.company` is the FQDN of the [Dex](https://dexidp.io/) container of the Terrakube installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Terrakube with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>terrakube-dex.company</em>/dex/callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Terrakube configuration

This guide assumes that you have environment variables `$TERRAKUBE_OIDC_CLIENT_ID` and `$TERRAKUBE_OIDC_CLIENT_SECRET` set up. You can hard-code values if your setup doesn’t support environment variables, but be aware that doing so is not recommended for security reasons.

1. **Locate the Dex Configuration File**
   Find the Dex configuration file, typically named `config.yaml` or `config.docker.yaml`. It’s usually located in the `/etc/dex` directory or the corresponding directory for a containerized setup.

2. **Update the Dex Configuration**
   To define the Terrakube OIDC connector, open the configuration file and add the following block:

    ```yaml
    connectors:
        - type: oidc
          id: TerrakubeClient
          name: TerrakubeClient
          config:
              issuer: "https://authentik.company/application/o/<Your application slug>/"
              clientID: $TERRAKUBE_OIDC_CLIENT_ID
              clientSecret: $TERRAKUBE_OIDC_CLIENT_SECRET
              redirectURI: "https://terrakube-dex.company/dex/callback"
              insecureEnableGroups: true
    ```

3. **Set Environment Variables**
   Add the following variables to your `.env` file, replacing them with the appropriate values for your Client ID and Client Secret:

    ```env
    TERRAKUBE_OIDC_CLIENT_ID=*your Client ID*
    TERRAKUBE_OIDC_CLIENT_SECRET=*your Client Secret*
    ```

## Configuration verification

To ensure that authentik is correctly configured with Terrakube, log out and log back in through authentik. Depending on the number of connectors you have set up, you should either be redirected to authentik or see a new button appear on the Dex login page.
