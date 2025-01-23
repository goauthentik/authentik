---
title: Integrate with Nextcloud
sidebar_label: Nextcloud
---

# Integrate with Nextcloud

<span class="badge badge--secondary">Support level: Community</span>

## What is Nextcloud

> Nextcloud is a suite of client-server software for creating and using file hosting services. Nextcloud is free and open-source, which means that anyone is allowed to install and operate it on their own private server devices.
>
> -- https://en.wikipedia.org/wiki/Nextcloud

:::caution
If you require [Server Side Encryption](https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/encryption_configuration.html), you must use LDAP. OpenID and SAML will cause **irrevocable data loss**. Nextcloud Server-Side Encryption requires access to the user's cleartext password, which Nextcloud only has access to when using LDAP as the user enters their password directly into Nextcloud.
:::

:::caution
This setup only works when Nextcloud is running with HTTPS enabled. See [here](https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/reverse_proxy_configuration.html?highlight=overwriteprotocol#overwrite-parameters) on how to configure this.
:::

:::info
In case something goes wrong with the configuration, you can use the URL `http://nextcloud.company/login?direct=1` to log in using the built-in authentication.
:::

## Authentication

There are 3 ways to setup single sign on (SSO) for Nextcloud:

- [via OIDC Connect (OAuth)](#openid-connect-auth)
- [via SAML](#saml-auth)
- via LDAP outpost (required for SSE, not covered in this documentation)

### OpenID Connect auth

#### Preparation

The following placeholders are used in this guide:

- `nextcloud.company` is the FQDN of the Nextcloud installation.
- `authentik.company` is the FQDN of the authentik installation.
- `authentik.local` is the internal FQDN of the authentik install (only relevant when running authentik and Nextcloud behind a reverse proxy)

Lets start by thinking what user attributes need to be available in Nextcloud:

- name
- email
- unique user ID
- storage quota (optional)
- groups (optional)

authentik already provides some default _scopes_ with _claims_ inside them, such as:

- `email` scope: Has claims `email` and `email_verified`
- `profile` scope: Has claims `name`, `given_name`, `preferred_username`, `nickname`, `groups`
- `openid` scope: This is a default scope required by the OpenID spec. It contains no claims

##### Custom profile scope

If you do not need storage quota, group information, or to manage already existing users in Nextcloud [skip to the next step](#provider-and-application).

However, if you want to be able to control how much storage users in Nextcloud can use, as well as which users are recognized as Nextcloud administrators, you would need to make this information available in Nextcloud. To achieve this you would need to create a custom `profile` scope. To do so, go to _Customization_ -> _Property mappings_. Create a _Scope mapping_ with the following parameters:

- Name: Nextcloud Profile
- Scope name: profile
- Expression:

```python
# Integrate with Extract all groups the user is a member of
groups = [group.name for group in user.ak_groups.all()]

# Integrate with Nextcloud admins must be members of a group called "admin".
# Integrate with This is static and cannot be changed.
# Integrate with We append a fictional "admin" group to the user's groups if they are an admin in authentik.
# Integrate with This group would only be visible in Nextcloud and does not exist in authentik.
if user.is_superuser and "admin" not in groups:
    groups.append("admin")

return {
    "name": request.user.name,
    "groups": groups,
    # To set a quota set the "nextcloud_quota" property in the user's attributes
    "quota": user.group_attributes().get("nextcloud_quota", None),
    # To connect an already existing user, set the "nextcloud_user_id" property in the
    # user's attributes to the username of the corresponding user on Nextcloud.
    "user_id": user.attributes.get("nextcloud_user_id", str(user.uuid)),
}
```

:::note
To set a quota set the "nextcloud_quota" property in the user's attributes. This can be set for individual users or a group of users, as long as the target user is a member of a group which has this attribute set.

If set to a value, for example `1 GB`, user(s) will have 1GB storage quota. If the attribute is not set, user(s) will have unlimited storage.
:::

:::note
To connect to an already existing Nextcloud user, set the "nextcloud_user_id" property in the user's attributes. This must be set for each individual user.

The value of `nextcloud_user_id` must match the field `username` of the user on the Nextcloud instance. On Nextcloud, go to _Users_ to see the username of the user you are trying to connect to (Under user's `Display name`).
If set to a value, for example `goauthentik`, it will try to connect to the `goauthentik` user on the Nextcloud instance. Otherwise, the user's UUID will be used.
:::

##### Provider and Application

Create a provider for Nextcloud. In the Admin Interface, go to _Applications_ -> _Providers_. Create an _OAuth2/OpenID Provider_ with the following parameters:

- Name: Nextcloud
- Client type: Confidential
- Redirect URIs/Origins (RegEx): `https://nextcloud.company/apps/user_oidc/code`
- Signing key: Any valid certificate
- Under advanced settings:
    - Scopes:
        - `authentik default Oauth Mapping email`
        - `Nextcloud Profile` (or `authentik default Oauth Mapping profile` if you skipped the [custom profile scope](#custom-profile-scope) section)
    - Subject mode: Based on the User's UUID
      :::danger
      Nextcloud will use the UUID as username. However, mapping the subject mode to authentik usernames is **not recommended** due to their mutable nature. This can lead to security issues such as user impersonation. If you still wish to map the subject mode to an username, [disable username changing](https://docs.goauthentik.io/docs/sys-mgmt/settings#allow-users-to-change-username) in authentik and set this to `Based on the User's username`.
      :::
    - Include claims in ID token: ✔️

Before continuing, make sure to take note of your `client ID` and `secret ID`. Don't worry you can go back to see/change them at any time.

:::note
There were an issue in the Nextcloud OIDC app that was [limiting the size of the secret ID](https://github.com/nextcloud/user_oidc/issues/405) token to 64 characters. This issue was fixed in December 2023, so make sure you update to the latest version of the [OpenID Connect user backend](https://apps.nextcloud.com/apps/user_oidc) application.
:::

:::note
Depending on your Nextcloud configuration, you might need to use `https://nextcloud.company/index.php/` instead of `https://nextcloud.company/`
:::

After the provider is created, link it to an app. Go to _Applications_ -> _Applications_. Create an application and choose the provider you just created. Make sure to take note of the _application slug_. You will need this later.

#### Nextcloud

In Nextcloud, ensure that the `OpenID Connect user backend` app is installed. Navigate to `Settings`, then `OpenID Connect`.

Add a new provider using the `+` button and set the following values:

- Identifier: Authentik
- Client ID: The client ID from the provider
- Client secret: The secret ID from the provider
- Discovery endpoint: `https://authentik.company/application/o/<nextcloud-app-slug>/.well-known/openid-configuration`
  :::tip
  If you are running both your authentik and Nextcloud instances behind a reverse proxy, you can go ahead and use your internal FQDN here (i.e. `http://authentik.local`, however, note that if you do so there is [extra configuration required](#extra-configuration-when-running-behind-a-reverse-proxy)).
  :::
- Scope: `email profile` (you can safely omit `openid` if you prefer)
- Attribute mappings:
    - User ID mapping: sub (or `user_id` if you need to connect to an already existing Nextcloud user)
    - Display name mapping: name
    - Email mapping: email
    - Quota mapping: quota (leave empty if you have skipped the [custom profile scope](#custom-profile-scope) section)
    - Groups mapping: groups (leave empty if you have skipped the [custom profile scope](#custom-profile-scope) section)
      :::tip
      You need to enable the "Use group provisioning" checkmark to be able to write to this field
      :::
- Use unique user ID: If you only have one provider you can deselect this if you prefer. This will affect your Federated Cloud ID, which you can check under _Personal settings_ -> _Sharing_ -> _Federated Cloud_. If the box is selected, nextcloud will pick a hashed value here (`437218904321784903214789023@nextcloud.instance` for example). Otherwise, it will use the mapped user ID (`<authentik's sub or user_id>@nextcloud.instance`).
  :::tip
  To avoid your federated cloud id being a hash value, deselect **Use unique user ID** and use `user_id` in the **User ID mapping** field.
  :::

At this stage you should be able to login with SSO.

##### Making the OIDC provider the default login method

If you intend to only login to Nextcloud using your freshly configured authentik provider, you may wish to make it the default login method. This will allow your users to be automatically redirected to authentik when they attempt to access your Nextcloud instance, as opposed to having to manually click on "Log in with Authentik" every time they wish to login.

To achieve this, you will need to use the `occ` command of your Nextcloud instance:

```bash
sudo -u www-data php var/www/nextcloud/occ config:app:set --value=0 user_oidc allow_multiple_user_backends
```

##### Extra configuration when running behind a reverse proxy

The OpendID Connect discovery endpoint is queried by Nextcloud and contains a list of endpoints for use by both the relying party (Nextcloud) and the authenticating user.

:::note
If you are configuring an insecure (http) discovery endpoint, Nextcloud will, by default, refuse to connect to it. To change this behaviour, you must add `allow_local_remote_servers => true` to your `config.php`
:::

:::note
It is currently not possible force Nextcloud to connect to an https endpoint which uses an untrusted (selfsigned) certificate. If this is the case with your setup, you can do one of 3 things:

- switch to using a trusted certificate
- add the selfsigned certificate to Nextcloud's trust store
- switch to using an http endpoint and add `allow_local_remote_servers => true` to your `config.php`

:::

Because authentik has no knowledge of where each endpoint is/can be accessed from, it will always return endpoints with domain names matching the one used to make the discovery endpoint request.

For example, if your Nextcloud instance queries the discovery endpoint using an internal domain name (`authentik.local`), all returned endpoints will have the same domain name. In this case:

- `http://authentik.local/application/o/<app-slug>/`
- `http://authentik.local/application/o/authorize/`
- `http://authentik.local/application/o/token/`
- `http://authentik.local/application/o/userinfo/`
- `http://authentik.local/application/o/<app-slug>/end-session/`
- `http://authentik.local/application/o/introspect/`
- `http://authentik.local/application/o/revoke/`
- `http://authentik.local/application/o/device/`
- `http://authentik.local/application/o/<app-slug>/jwks/`

This represents a problem, because Nextcloud will attempt to redirect the user to the received `authorization` and `end-session` endpoints during login and logout respectively. When that happens, the user will try to access an internal domain and fail.

The easiest way to fix this is to modify the redirect response's `Location` header coming back from Nextcloud during login and logout. Different proxies have different ways of achieving this. For example with Traefik, a 3rd party plugin called [Rewrite Header](https://plugins.traefik.io/plugins/628c9eb5108ecc83915d7758/rewrite-header) can be used.

At a minimum, the `authorize` and `end-session` endpoints must be edited in-flight like so:

- `http://authentik.local/application/o/authorize/` -> `https://authentik.company/application/o/authorize/`
- `http://authentik.local/application/o/<app-slug>/end-session/` -> `https://authentik.company/application/o/<app-slug>/end-session/`

:::note
HTTP headers are usually capitalised (e.g. **L**ocation), however, at least some versions of Nextcloud seem to return all lowercase headers (e.g. **l**ocation). To be safe, make sure to add header replacement rules for both cases.
:::

If you prefer, you may also edit the rest of the endpoints, though that should not be necessary, as they should not be accessed by the user.

:::tip
If you do not have any relying parties accessing authentik from the outside, you may also configure your proxy to only allow access to the `authorize` and `end-session` endpoints from the outside world.
:::

### SAML auth

#### Preparation

The following placeholders are used in this guide:

- `nextcloud.company` is the FQDN of the Nextcloud installation.
- `authentik.company` is the FQDN of the authentik installation.

Create an application in authentik and note the slug you choose, as this will be used later. In the Admin Interface, go to _Applications_ -> _Providers_. Create a _SAML provider_ with the following parameters:

- ACS URL: `https://nextcloud.company/apps/user_saml/saml/acs`
- Issuer: `https://authentik.company`
- Service Provider Binding: `Post`
- Audience: `https://nextcloud.company/apps/user_saml/saml/metadata`
- Signing certificate: Select any certificate you have.
- Property mappings: Select all Managed mappings.

:::note
Depending on your Nextcloud configuration, you might need to use `https://nextcloud.company/index.php/` instead of `https://nextcloud.company/`
:::

You can of course use a custom signing certificate, and adjust durations.

#### Nextcloud

In Nextcloud, ensure that the `SSO & SAML Authentication` app is installed. Navigate to `Settings`, then `SSO & SAML Authentication`.

Set the following values:

- Attribute to map the UID to: `http://schemas.goauthentik.io/2021/02/saml/uid`
  :::danger
  Nextcloud uses the UID attribute as username. However, mapping it to authentik usernames is **not recommended** due to their mutable nature. This can lead to security issues such as user impersonation. If you still wish to map the UID to an username, [disable username changing](https://docs.goauthentik.io/docs/sys-mgmt/settings#allow-users-to-change-username) in authentik and set the UID attribute to "http://schemas.goauthentik.io/2021/02/saml/username".
  :::
- Optional display name of the identity provider (default: "SSO & SAML log in"): `authentik`
- Identifier of the IdP entity (must be a URI): `https://authentik.company`
- URL Target of the IdP where the SP will send the Authentication Request Message: `https://authentik.company/application/saml/<application-slug>/sso/binding/redirect/`
- URL Location of IdP where the SP will send the SLO Request: `https://authentik.company/application/saml/<application-slug>/slo/binding/redirect/`
- Public X.509 certificate of the IdP: Copy the PEM of the Selected Signing Certificate

Under Attribute mapping, set these values:

- Attribute to map the displayname to.: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
- Attribute to map the email address to.: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
- Attribute to map the users groups to.: `http://schemas.xmlsoap.org/claims/Group`

You should now be able to log in with authentik.

:::note
If Nextcloud is behind a reverse proxy you may need to force Nextcloud to use HTTPS.
To do this you will need to add the line `'overwriteprotocol' => 'https'` to `config.php` in the Nextcloud `config\config.php` file
See https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/reverse_proxy_configuration.html#overwrite-parameters for additional information
:::

#### Group Quotas

Create a group for each different level of quota you want users to have. Set a custom attribute, for example called `nextcloud_quota`, to the quota you want, for example `15 GB`.

Afterwards, create a custom SAML Property Mapping with the name `SAML Nextcloud Quota`.

- Set the _SAML Attribute Name_ to `nextcloud_quota`.
- Set the _Expression_ to:

```python
return user.group_attributes().get("nextcloud_quota", "1 GB")
```

where `1 GB` is the default value for users that don't belong to another group (or have another value set).

Then, edit the Nextcloud SAML Provider, and add `nextcloud_quota` to Property mappings.

In Nextcloud, go to `Settings`, then `SSO & SAML Authentication`Under `Attribute mapping`, set this value:

- Attribute to map the quota to.: `nextcloud_quota`

#### Admin Group

To give authentik users admin access to your Nextcloud instance, you need to create a custom Property Mapping that maps an authentik group to "admin". It has to be mapped to "admin" as this is static in Nextcloud and cannot be changed.

Create a custom SAML Property Mapping:

- Set the _SAML Attribute Name_ to `http://schemas.xmlsoap.org/claims/Group`.
- Set the _Expression_ to:

```python
for group in request.user.all_groups():
    yield group.name
if ak_is_group_member(request.user, name="<authentik nextcloud admin group's name>"):
    yield "admin"
```

Then, edit the Nextcloud SAML Provider, and replace the default Groups mapping with the one you've created above.
