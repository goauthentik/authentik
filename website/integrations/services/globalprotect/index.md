---
title: Integrate with GlobalProtect
sidebar_label: GlobalProtect
support_level: community
---

## What is GlobalProtect

> GlobalProtect enables you to use Palo Alto Networks next-gen firewalls or Prisma Access to secure your mobile workforce.
>
> Palo Alto Networks GlobalProtect platform is a paid enterprise product.
>
> -- https://docs.paloaltonetworks.com/globalprotect

## Preparation

The following placeholders are used in this guide:

- `gp.company` is the FQDN of the GlobalProtect portal.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::caution
A trusted web certificate is required to be bound to the GlobalProtect Portal. This can be signed by a trusted internal Root Certificate Authority (CA); however, a self signed certificate, a certificate outside of its validity, or a non-standard confirming certificate (such as a lifespan not trusted by modern browsers) will error out on SAML authentication.
:::

## authentik Configuration

To support the integration of GlobalProtect with authentik, you need to create an application/provider pair in authentik.

### Create an Application and Provider in authentik

1. Log in to authentik as an admin and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: Provide a descriptive name, an optional group, and UI settings. Take note of the **slug** as it will be required later.
    - **Choose a Provider type**: Select **SAML Provider**.
    - **Configure the Provider**:
        - Set the **ACS URL** to <kbd>https://<em>gp.company:443</em>/SAML20/SP/ACS</kbd>. (Note the absence of the trailing slash and the inclusion of the web interface port)
        - Set the **Issuer** to <kbd>https://<em>authentik.company</em>/application/saml/<em>application-slug</em>/sso/binding/redirect/</kbd>.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**, select an available signing certificate.
3. Click **Submit** to save the new application and provider.

### Download the metadata

1. Log in to authentik as an admin and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** > **_Provider Name_** and download the SAML metadata.

## GlobalProtect configuration

1. Navigate to the GlobalProtect configuration device (Firewall or Panorama).

2. Navigate to 'SAML Identity Provider' on the Device tab and choose the 'import' option.

- Provide a name for the profile.
- Import the metadata file downloaded earlier. (This will automatically install the authentik signing certificate to the system upon commit.)
- Select 'Validate Identity Provider Certificate' if desired.

3. Navigate to 'Authentication Profile' on the Device tab and add a new profile.

- Type: SAML
- IdP Server Profile: The profile just created
- Certificate for Signing Requests: None (Optionally configure authentik for mutual SAML signature)
- Certificate Profile: None (Optionally configure profile to validate the authentik signing cert)
- Username Attribute: `username`

4. Chose 'Advanced' within the profile and add 'all'. This will have only authentik control the authorization.

5. Navigate to the 'GlobalProtect Portal Configuration' and chose the portal for SAML access.

- Under 'Authentication' select the 'Authentication Profile' to the one just created. Leave all other settings as default.
- Optionally chose to require client access via separately issued client cert as well. If not using a client cert, select 'Yes (User Credentials OR Client Certificate Required)'.

6. Make the same exact changes to the 'GlobalProtect Gateway Configuration'.

7. Commit the changes to the firewall.
