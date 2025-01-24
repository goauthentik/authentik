---
title: Integrate with GlobalProtect
sidebar_label: GlobalProtect
---

# GlobalProtect

<span class="badge badge--secondary">Support level: Community</span>

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

:::caution
A trusted web certificate is required to be bound to the GlobalProtect Portal. This can be signed by a trusted internal Root Certificate Authority (CA); however, a self signed certificate, a certificate outside of its validity, or a non-standard confirming certificate (such as a lifespan not trusted by modern browsers) will error out on SAML authentication.
:::

## authentik configuration

1. In the Admin interface of authentik, under _Providers_, create a SAML provider with these settings:

- ACS URL: `https://gp.company:443/SAML20/SP/ACS` (Note the absence of the trailing slash, and the inclusion of the web interface port)
- Issuer: `https://authentik.company/application/saml/fgm/sso/binding/redirect/`
- Service Provider Binding: Post
- You can of course use a custom signing certificate, and adjust durations.

2.  Select the newly created Provider and download the metadata using the tool on the 'Overview' tab.

3.  In the Admin interface of authentik, under _Application_, create an application with these settings:

- Launch URL: `blank://blank` (This setting hides the application, while still granting access)
- Use the _Provider_ and _Slug_ previously set in the first step.

4. Set the bindings appropriately to those who will be allowed to authenticate.

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
