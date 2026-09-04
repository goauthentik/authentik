---
title: Integrate with Red Hat Ansible Automation Platform / AWX
sidebar_label: Red Hat Ansible Automation Platform / AWX
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Red Hat Ansible Automation Platform / AWX?

> Red Hat Ansible Automation Platform and AWX provide web interfaces, APIs, and automation services for running, scheduling, and managing Ansible automation across infrastructure and applications.
>
> -- https://www.redhat.com/en/technologies/management/ansible

## Preparation

The following placeholders are used in this guide:

- `automation.company` is the FQDN of the Red Hat Ansible Automation Platform or AWX installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info Version paths
AWX and automation controller in Red Hat Ansible Automation Platform 2.4 and earlier use the controller SAML settings. Red Hat Ansible Automation Platform 2.5 and newer use platform gateway authentication methods.
:::

Create or identify the SAML service provider certificate and private key that Red Hat Ansible Automation Platform or AWX will use for its own SAML service provider configuration. This is separate from the authentik signing certificate that you download later.

```shell
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes
```

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Red Hat Ansible Automation Platform or AWX with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because you will use it later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - If you are configuring AWX or automation controller, set **ACS URL** to `https://automation.company/sso/complete/saml/`.
        - If you are configuring Red Hat Ansible Automation Platform 2.5 or newer, set **ACS URL** to `https://temp.temp`. You will update this value after creating the authentication method in Red Hat Ansible Automation Platform.
        - Set **Audience** to `https://automation.company`.
        - Under **Advanced protocol settings**, select an available **Signing Certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Create Application** to save the new application and provider.

### Copy the SAML values

1. In the authentik Admin interface, navigate to **Applications** > **Providers** and open the SAML provider that you created.
2. Copy the **EntityID/Issuer** value.
3. Copy the **SAML Endpoint** value.
4. Under **Related objects** > **Download signing certificate**, click **Download**.

## Red Hat Ansible Automation Platform / AWX configuration

Use the subsection that matches your installation.

### Configure AWX or automation controller

1. Log in to AWX or automation controller as an administrator.
2. Navigate to **Settings** and select **SAML settings** from the authentication settings.
3. Click **Edit**.
4. Set **SAML Service Provider Entity ID** to `https://automation.company`.
5. Set **SAML Service Provider Public Certificate** to the full contents of the service provider certificate that you created during preparation, including the `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines.
6. Set **SAML Service Provider Private Key** to the full contents of the service provider private key that you created during preparation, including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines.
7. Set **SAML Service Provider Organization Info** to the following value:

    ```json
    {
        "en-US": {
            "name": "authentik",
            "url": "https://authentik.company",
            "displayname": "authentik"
        }
    }
    ```

8. Set **SAML Service Provider Technical Contact** and **SAML Service Provider Support Contact** to the appropriate contact information for your environment:

    ```json
    {
        "givenName": "Admin Name",
        "emailAddress": "admin@company"
    }
    ```

9. Set **SAML Enabled Identity Providers** to the following value. Replace `<Signing certificate from authentik without PEM headers>` with the downloaded authentik signing certificate, with the `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines removed and the certificate entered as one line.

    ```json
    {
        "authentik": {
            "entity_id": "<EntityID/Issuer from authentik>",
            "url": "<SAML Endpoint from authentik>",
            "x509cert": "<Signing certificate from authentik without PEM headers>",
            "attr_username": "http://schemas.goauthentik.io/2021/02/saml/username",
            "attr_user_permanent_id": "http://schemas.goauthentik.io/2021/02/saml/uid",
            "attr_email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "attr_first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
        }
    }
    ```

10. Click **Save**.

### Configure Red Hat Ansible Automation Platform 2.5 or newer

1. Log in to Red Hat Ansible Automation Platform as an administrator.
2. Navigate to **Access Management** > **Authentication Methods**.
3. Click **Create authentication**.
4. Enter a name for the SAML configuration.
5. Set **Authentication type** to **SAML**.
6. Set **SAML Service Provider Entity ID** to `https://automation.company`.
7. Set **SAML Service Provider Public Certificate** to the full contents of the service provider certificate that you created during preparation, including the `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines.
8. Set **SAML Service Provider Private Key** to the full contents of the service provider private key that you created during preparation, including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines.
9. Set **IdP Login URL** to the **SAML Endpoint** value from authentik.
10. Set **IdP Public Cert** to the full PEM certificate that you downloaded from authentik.
11. Set **Entity ID** to the **EntityID/Issuer** value from authentik.
12. Configure the user attribute fields:
    - **Groups**: `http://schemas.xmlsoap.org/claims/Group`
    - **User Email**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
    - **Username**: `http://schemas.goauthentik.io/2021/02/saml/username`
    - **User First Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
    - **User Permanent ID**: `http://schemas.goauthentik.io/2021/02/saml/uid`
13. Leave **SAML Assertion Consumer Service (ACS) URL** blank. Red Hat Ansible Automation Platform generates this value after you create the authentication method.
14. Set **SAML Service Provider Organization Info** to the following value:

    ```json
    {
        "en-US": {
            "name": "authentik",
            "url": "https://authentik.company",
            "displayname": "authentik"
        }
    }
    ```

15. Set **SAML Service Provider Technical Contact** and **SAML Service Provider Support Contact** to the appropriate contact information for your environment:

    ```json
    {
        "givenName": "Admin Name",
        "emailAddress": "admin@company"
    }
    ```

16. Select **Enabled**.
17. Click **Create Authentication Method**.
18. Open the authentication method that you created and copy the generated **SAML Assertion Consumer Service (ACS) URL**.

### Update the authentik provider

Complete this subsection only for Red Hat Ansible Automation Platform 2.5 or newer.

1. In the authentik Admin interface, navigate to **Applications** > **Providers** and open the SAML provider that you created.
2. Click **Edit**.
3. Set **ACS URL** to the generated **SAML Assertion Consumer Service (ACS) URL** from Red Hat Ansible Automation Platform.
4. Click **Save Changes**.

## Configuration verification

To confirm that authentik is properly configured with Red Hat Ansible Automation Platform or AWX, open the integration and sign in with SAML.

## Resources

- [AWX documentation - Setting up Enterprise Authentication](https://docs.ansible.com/projects/awx/en/24.6.1/administration/ent_auth.html)
- [Red Hat Ansible Automation Platform 2.6 - Configure SAML authentication](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/secure-proc_controller_set_up_saml)
- [Red Hat Ansible Automation Platform 2.4 - Setting up enterprise authentication](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.4/html/automation_controller_administration_guide/controller-set-up-enterprise-authentication)
