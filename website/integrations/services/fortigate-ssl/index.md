---
title: Integrate with FortiGate SSLVPN
sidebar_label: FortiGate SSLVPN
---

# Integrate with FortiGate SSLVPN

<span class="badge badge--secondary">Support level: Community</span>

## FortiGate SSLVPN

> FortiGate is a firewall from FortiNet. It is a NGFW with layer7 inspection and able to become a part of a FortiNet security fabric.
> -- https://www.fortinet.com/products/next-generation-firewall
>
> This guide explains how to setup a FortiGate to use authentik with a SAML provider for SSLVPN authentication. It does not cover how to setup SAML for admin logins, that is a different configuration. If you need to setup SAML for admin logins see the FortiGate admin guide.
>
> This guide has been created using the following software versions. Instructions may differ between versions.
>
> - Fortigate: 7.2.8
> - authentik: 2024.2.2

## Assumptions

- You know how to configure an SSLVPN in a FortiGate.
- You already have a certificate for signing and encryption uploaded to both authentik and the FortiGate.
- You already have a working SSLVPN (either portal or tunnel) and is just changing authentication from what you are using today to authentik SAML.

The following placeholders are used in this guide:

- `saml.sp.name` = The name that will be the SAML SP configuration in the FortiGate
- `fgt.cert` = Fortigate certificate for signing and encrypting
- `service.company` = This is the FQDN of the firewall, if your sslvpn portal is not on TCP port 443, then add the port like: fortigate.mydomain.tld:10233
- `authentik.company` = This is the FQDN of your authentik installation
- `app.slug.name` = The application slug that you decided upon
- `ak.cert` = The authentik remote certificate you have uploaded before starting the guide.
- `fgt.user.group` = This will be the name of the user group in your Fortigate that you will use in your SSLVPN portal mapping and Firewall rules
- `ak.user.group` = This is the user group name that you will use in authentik if you plan on limiting access to the sslvpn via groups.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## FortiGate configuration

### Preparation

- Decide on an application name (slug) e.g. fgtsslvpn that you will use in authentik later.

### Setup SAML SP

1.  SSH to the Fortigate (If you are using vdom change to the correct vdom).
2.  Copy the config below to your preferred editor and change the placeholders to your settings, then paste it into the Fortigate.

> [!NOTE]
> Some are https and some are http, that is on purpose, and as described by FortiNet.

```
config user saml
    edit "saml.sp.name"
        set cert "fgt.cert"
        set entity-id "http://service.company/remote/saml/metadata/"
        set single-sign-on-url "https://service.company/remote/saml/login"
        set single-logout-url "https://service.company/remote/saml/logout"
        set idp-entity-id "https://authentik.company"
        set idp-single-sign-on-url "https://authentik.company/application/saml/app.slug.name/sso/binding/redirect/"
        set idp-single-logout-url "https://authentik.company/application/saml/app.slug.name/slo/binding/redirect/"
        set idp-cert "ak.cert"
        set user-name "http://schemas.goauthentik.io/2021/02/saml/username"
        set group-name "http://schemas.xmlsoap.org/claims/Group"
        set digest-method sha256
    next
end
```

### Add the SAML single sign-on to a user group

This will limit who can login via authentik SAML. It will match on `ak.user.group` which is the group you will set up in authentik later, and only allow users of that group to login. In essence it provides the same functionality as returning a user-group via Radius, and matching on the user group.

```
config user group
    edit "fgt.user.group"
        set member "saml.sp.name"
        config match
            edit 1
                set server-name "saml.sp.name"
                set group-name "ak.user.group"
            next
        end
    next
end
```

> [!IMPORTANT]
> If you created a new firewall group, instead of using an existing sslvpn firewall group, then remember to map it to a portal in the 'SSL-VPN Settings' page, and add the `fgt.user.group` to firewall rules, or you will be redirected back to authentik with a logout immediately upon each login attempt.

Next get the metadata from the FortiGate to help us with the SAML configuration in authentik. Copy all the output from the command below and save it in a xml file named `fgt-metadata.xml`. You will upload that to authentik later, to facilitate auto-configuration.

```
diag vpn ssl saml-metadata saml.sp.name
```

## authentik setup

It's time to log in to authentik and set up the provider and application.

## Provider section

Let's set up the provider using the SAML metadata from the FortiGate.

### Setup the provider using metadata

- Go to **Applications -> Providers**.
- Click **Create**.
- Select **SAML Provider from Metadata** at the bottom.
    - Name: Name it something appropriate e.g. FGT SSL SAML Provider
    - Authorization flow: default-provider-authorization-implicit-consent (Authorize Application)
    - Metadata: upload the fgt-metadata.xml you created previously
- Click **Finish**.

### Validate and change settings for provider

- Click the Edit icon to the right of the provider you just created, under the **Actions** column..
    - Authentication flow = default-authentication-flow (Welcome to authentik!)
    - ACS URL = https://service.company/remote/saml/login
    - Issuer = https://authentik.company
    - Service Provider Binding = POST
    - Audience = http://service.company/remote/saml/metadata/
    - Signing certificate = ak.cert
    - Verification Certificate = Should already be filled with the certificate from the metadata you uploaded.
    - Property mapping:
        - authentik default SAML Mapping: Username
        - authentik default SAML Mapping: Groups
    - Named Property Mapping: Empty (------)
    - Assertion valid not before = minutes=5
    - Assertion valid not on or after = minutes=5
    - Session valid not on or after = (Set how long you want the user's session to be valid)
    - Default relay state = empty
    - Digest algorithm = sha256
    - Signature algorithm = sha256

## Application section

Lets create the application and link it to the provider.

### Create user group

This is the user group that you matched on in the FortiGate "firewall group" above.

- Go to **Directory -> Groups**.
- Click **Create**.
- Name = `ak.user.group`.
- Open ak.user.group and add the users whom should have access to the sslvpn.
- Save the group.

### Create the application

> [!NOTE]
> The Launch URL = blank://blank will prevent authentik from displaying it on the user's login page in authentik.

- Go to **Applications -> Applications**.
- Name = Whatever you fancy e.g. FGT-SSLVPN
- Slug = app.slug.name
- Group = empty (------)
- Provider = The provider you created before e.g. "FGT SSL SAML Provider"
- Backchannel Provider = empty (-----)
- Policy engine mode = any
- Launch URL = blank://blank
- Open in new tab = disabled
- icon = None
- Publisher = None
- Description = None
- Click **Save**.

### Limiting the access based on authentik group

- Open the application again
- Click on "Policy / Group / User Binding"
- Click **Bind existing policy**.
- Click on **Group** in the tabs at the top.
- In the **Group** drop-down menu, select `ak.user.group`.
- Make sure that **Enabled** is chosen.
- Order = 10
- Timeout = 30
- Failure result = Don't pass
- Click **Create**.

You should now be able to log in by selecting SSO login either on the portal or in FortiClient, depending on your portal configuration.

> [!NOTE]
> If you are using FortiClient remember to set the sslvpn profile to use single sign-on either creating a manual profile or editing the profile in your EMS.

## Troubleshooting

These are just suggestions of what **could** be the cause of an issue and how to enable debug on the FortiGate.

> [!CAUTION]
> Debugging can generate heavy load on a FortiGate firewall, so make sure your firewall is not already struggling with performance before you enable debugging, and remember to disabled it again when you are done.
>
> You can disable the debug with these commands.
> `diag debug disable` > `diag debug reset`

### Enabling debug output

Before you can see any output you need to enable the debug mode.
`diagnose debug enable`

### Debug saml daemon

This will provide all possible output from the SAML daemon.
`diag debug application samld -1`

### Debug sslvpn (optional)

This will provide insight into what happens when you use FortiClient, usually combined with `salmd debug`.
`diag debug application sslvpn -1`

### Debug https daemon (optional)

This can be used to see what calls are made when using the SSLVPN portal. Note this will also catch any admins working on the firewall and can get a bit messy.\
`diag debug application httpsd -1`

### Enable debug timestamps (optional)

Provides timestamp on the debug output lines\
`diagnose debug console timestamp enable`

### Error: Assertion failed with url

This could be caused by a time difference between SP and IDP

### Error: Assertion failed with 'coin'

You have not set the audience in the SAML provider settings

### Error: Redirection loop

This could be caused by the `fgt.user.group` not being added to any firewall rules.

### Error: Redirected to logout page on authentik when logging in

User group `fgt.user.group` is not mapped to any portals ( Fortigate settings page 'SSL-VPN Settings'), and your default catch all does not allow access to either portal or tunnel.

### Error: authentik page shows "missing post data"

An error message about missing data is displayed by authentik. This error means you have used the wrong `idp-single-sign-on-url` and most likely the wrong `idp-single-logout-url` in the FortiGate SAML SP configuration. These should be the redirect URLs from authentik's provider configuration and not the post URLs.
