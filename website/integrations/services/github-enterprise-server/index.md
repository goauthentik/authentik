---
title: Integrate with GitHub Enterprise Server
sidebar_label: GitHub Enterprise Server
---

# Integrate with GitHub Enterprise Server

<span class="badge badge--secondary">Support level: Community</span>

## What is GitHub Enterprise Server

> GitHub Enterprise Server is a self-hosted platform for software development within your enterprise. Your team can use GitHub Enterprise Server to build and ship software using Git version control, powerful APIs, productivity and collaboration tools, and integrations. Developers familiar with GitHub.com can onboard and contribute seamlessly using familiar features and workflows.
>
> -- https://docs.github.com/en/enterprise-server@3.5/admin/overview/about-github-enterprise-server

## Preparation

The following placeholders are used in this guide:

- `https://github.company` is your GitHub Enterprise Server installation
- `authentik.company` is the FQDN of the authentik Install
- `GitHub Users` is an authentik group used for holding GitHub users.
- `GitHub Admins` is an authentik group used for indicating GitHub administrators.

First, create the two groups, in authentik, go to _Groups_, click _Create_ and put in `GitHub Users`, or your chosen user group name. Repeat this step with your Admin group as well.

Create a SAML provider with the following parameters:

- ACS URL: `https://github.company/saml/consume`
- Audience: `https://github.company`
- Issuer: `https://github.company`
- Binding: `Post`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.

Once the provider is created, it is advised to download the signing certificate as you will need it later.

Create a matching application for your SAML provider.

## SAML Configuration

If you are planning to use SCIM, (available from GHES 3.14.0) you should create a first admin user on your instance and go to your personal access tokens at `https://github.company/settings/tokens/new`, click _Generate new token_ and click _Generate new token (classic)_. Your token should have a descriptive name and ideally, no expiration date. For permission scopes, you need to select _admin:enterprise_. Click _Generate token_ and store the resulting token in a safe location.

To enable SAML, navigate to your appliance maintenance settings. These are found at `https://github.company:8443`. Here, sign in with an administrator user and go to the Authentication section.

On this page:

- Select the _SAML_ option.
- In _Sign on URL_, input your _SSO URL (Redirect)_ from authentik.
- For _Issuer_, use the _Audience_ you set in authentik.
- Verify that the _Signature method_ and _Digest method_ match your SAML provider settings in authentik.
- For _Validation certificate_, upload the signing certificate you downloaded after creating the provider.
- If you plan to enable SCIM, select _Allow creation of accounts with built-in authentication_ and _Disable administrator demotion/promotion_ options. These are selected so you can use your admin user as an emergency non-SSO account, as well as create machine users, and to ensure users are not promoted outside your IdP.
- In the _User attributes_ section, enter `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` in the _Username_ field to ensure the emails become normalized into usernames in GitHub.
- Press Save settings on the left-hand side and wait for the changes to apply.

![Screenshot showing populated GitHub Enterprise Server SAML settings](ghes_saml_settings.png)

Once the appliance has saved the settings and reloaded the services, you should be able to navigate to your instance URL at `https://github.company` and sign in with SAML.

## SCIM Configuration

This section only applies if you have taken the steps prior to prepare the instance for SCIM enablement.

After enabling SAML, log into your initial admin account again. Click the user portrait in tee top right, click _Enterprise settings_, click _Settigs_ in the left-hand sidebar, click _Authentication security_. On this page you have to check _Enable SCIM configuration_ and press _Save_. After which you should get a message reading _SCIM Enabled_.

Before we create a SCIM provider, we have to create a new Property Mapping. In authentik, go to _Customization_, then _Property Mappings_. Here, click _Create_, select _SCIM Provider Mapping_. Name the mapping something memorable and paste the following code in the _Expression_ field:

```python
roles = []
# Integrate with Edit this if statement if you need to add more GitHub roles.
# Integrate with Valid roles include:
# Integrate with user, guest_collaborator, enterprise_owner, billing_manager
if ak_is_group_member(request.user, name='GitHub Admins'):
    roles.append({'value': 'enterprise_owner', 'primary': True})
else:
    roles.append({'value': 'user', 'primary': True})

return {
    "roles": roles,
}
```

If you named your group anything other than `GitHub Admins`, please ensure you change it in the code above.

Create a new SCIM provider with the following parameters:

- URL: `https://github.company/api/v3/scim/v2`
- Token: Paste the token you generated earlier here.
- In the _User filtering_ section, you can select your `GitHub Users` group.
- In the _Attribute mapping_ section, de-select the `authentik default SCIM Mapping: User` mapping from the _User Property Mappings_ by selecting it on the right-hand side and clicking the left-facing single chevron.
- Select the property mapping you created in the previous step and add it by clicking the right-facing single chevron.
- Ensure that `authentik default SCIM Mapping: Group` is the only one active in the _Group Property Mappings_.
- Click _Finish_.

Go back to your GitHub Enterprise Server Application created in the first step and add your new SCIM provider in the _Backchannel Providers_ field, then click the _Update_ button.

You should now be ready to assign users to your _GitHub Users_ and _GitHub Admins_ groups, which will be provisioend by the SCIM provisioner. If you do not see your users being provisioned, go to your SCIM provider and click the _Run sync again_ option. A few seconds later, you should see results of the SCIM sync.
