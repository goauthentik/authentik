---
title: Terrakube
sidebar_label: Terrakube
---

# Terrakube

<span class="badge badge--secondary">Support level: Community</span>

## What is Terrakube

> Terrakube is an open-source collaboration platform designed for managing remote Infrastructure-as-Code (IaC) operations with Terraform. It serves as a alternative to proprietary tools like Terraform Enterprise.
>
> -- https://terrakube.io/

## Preparation

The following placeholders are used in this guide:

- `terrakube-dex.company` is the FQDN of the [Dex](https://dexidp.io/) container of the Terrakube install.
- `authentik.company` is the FQDN of the authentik install.

## authentik configuration

1. From the Admin interface, navigate to **Applications** -> **Applications**.
2. Use the wizard to create a new application and provider. During this process:
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to ` https://terrakube-dex.company/dex/callback`.
    - Select any available signing key.

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
