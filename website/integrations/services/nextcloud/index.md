---
title: Nextcloud
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Nextcloud

> Nextcloud is a suite of client-server software for creating and using file hosting services. Nextcloud is free and open-source, which means that anyone is allowed to install and operate it on their own private server devices.
>
> -- https://en.wikipedia.org/wiki/Nextcloud

:::caution
This setup only works, when Nextcloud is running with HTTPS enabled. See [here](https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/reverse_proxy_configuration.html?highlight=overwriteprotocol#overwrite-parameters) on how to configure this.
:::

:::info
In case something goes wrong with the configuration, you can use the URL `http://nextcloud.company/login?direct=1` to log in using the built-in authentication.
:::

## Preparation

The following placeholders will be used:

-   `nextcloud.company` is the FQDN of the Nextcloud install.
-   `authentik.company` is the FQDN of the authentik install.

Create an application in authentik and note the slug you choose, as this will be used later. In the Admin Interface, go to _Applications_ -> _Providers_. Create a _SAML provider_ with the following parameters:

-   ACS URL: `https://nextcloud.company/apps/user_saml/saml/acs`
-   Issuer: `https://authentik.company`
-   Service Provider Binding: `Post`
-   Audience: `https://nextcloud.company/apps/user_saml/saml/metadata`
-   Signing certificate: Select any certificate you have.
-   Property mappings: Select all Managed mappings.

:::note
Depending on your Nextcloud configuration, you might need to use `https://nextcloud.company/index.php/` instead of `https://nextcloud.company/`
:::

You can of course use a custom signing certificate, and adjust durations.

## Nextcloud

In Nextcloud, ensure that the `SSO & SAML Authentication` app is installed. Navigate to `Settings`, then `SSO & SAML Authentication`.

Set the following values:

-   Attribute to map the UID to: `http://schemas.goauthentik.io/2021/02/saml/uid`
    :::danger
    Nextcloud uses the UID attribute as username. However, mapping it to authentik usernames is **not recommended** due to their mutable nature. This can lead to security issues such as user impersonation. If you still wish to map the UID to an username, [disable username changing](../../../docs/installation/configuration#authentik_default_user_change_username) in authentik and set the UID attribute to "http://schemas.goauthentik.io/2021/02/saml/username".
    :::
-   Optional display name of the identity provider (default: "SSO & SAML log in"): `authentik`
-   Identifier of the IdP entity (must be a URI): `https://authentik.company`
-   URL Target of the IdP where the SP will send the Authentication Request Message: `https://authentik.company/application/saml/<application-slug>/sso/binding/redirect/`
-   URL Location of IdP where the SP will send the SLO Request: `https://authentik.company/application/saml/<application-slug>/slo/binding/redirect`
-   Public X.509 certificate of the IdP: Copy the PEM of the Selected Signing Certificate

Under Attribute mapping, set these values:

-   Attribute to map the displayname to.: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
-   Attribute to map the email address to.: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
-   Attribute to map the users groups to.: `http://schemas.xmlsoap.org/claims/Group`

You should now be able to log in with authentik.

:::note
If Nextcloud is behind a reverse proxy you may need to force Nextcloud to use HTTPS.
To do this you will need to add the line `'overwriteprotocol' => 'https'` to `config.php` in the Nextcloud `config\config.php` file
See https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/reverse_proxy_configuration.html#overwrite-parameters for additional information
:::

## Group Quotas

Create a group for each different level of quota you want users to have. Set a custom attribute, for example called `nextcloud_quota`, to the quota you want, for example `15 GB`.

Afterwards, create a custom SAML Property Mapping with the name `SAML Nextcloud Quota`.

-   Set the _SAML Attribute Name_ to `nextcloud_quota`.
-   Set the _Expression_ to:

```python
return user.group_attributes().get("nextcloud_quota", "1 GB")
```

where `1 GB` is the default value for users that don't belong to another group (or have another value set).

Then, edit the Nextcloud SAML Provider, and add `nextcloud_quota` to Property mappings.

In Nextcloud, go to `Settings`, then `SSO & SAML Authentication`Under `Attribute mapping`, set this value:

-   Attribute to map the quota to.: `nextcloud_quota`

## Admin Group

To give authentik users admin access to your Nextcloud instance, you need to create a custom Property Mapping that maps an authentik group to "admin". It has to be mapped to "admin" as this is static in Nextcloud and cannot be changed.

Create a custom SAML Property Mapping:

-   Set the _SAML Attribute Name_ to `http://schemas.xmlsoap.org/claims/Group`.
-   Set the _Expression_ to:

```python
for group in user.ak_groups.all():
    yield group.name
if ak_is_group_member(request.user, name="<authentik nextcloud admin group's name>"):
    yield "admin"
```

Then, edit the Nextcloud SAML Provider, and replace the default Groups mapping with the one you've created above.
