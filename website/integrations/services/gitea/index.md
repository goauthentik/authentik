---
title: Gitea
---

## What is Gitea

From https://gitea.io/

:::note
Gitea is a community managed lightweight code hosting solution written in Go. It is published under the MIT license.
:::

:::note
This is based on authentik 2021.10.3 and Gitea 1.15.6 installed using https://docs.gitea.io/en-us/install-from-binary/. Instructions may differ between versions.
:::

## Preparation

The following placeholders will be used:

- `authentik.company` is the FQDN of authentik.
- `gitea.company` is the FQDN of Gitea.

### Step 1

In authentik, create an _OAuth2/OpenID Provider_ (under _Resources/Providers_) with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**
- Name: Gitea
- RSA Key: authentik Self-signed certificate

:::note
Take note of the `Client ID` and `Client Secret`, you'll need to give them to Gitea in _Step 3_.
:::

### Step 2

In authentik, create an application (under _Resources/Applications_) which uses this provider. Optionally apply access restrictions to the application using policy bindings.

:::note
Only settings that have been modified from default have been listed.
:::

- Name: Gitea
- Slug: gitea-slug
- Provider: Gitea

### Step 3

Navigate to the _Authentication Sources_ page at https://gitea.company/admin/auths and click `Add Authentication Source`

Change the following fields

- Authentication Name: authentik
- OAuth2 Provider: OpenID Connect
- Client ID (Key): Step 2
- Client Secret: Step 2
- Icon URL: https://raw.githubusercontent.com/goauthentik/authentik/master/web/icons/icon.png
- OpenID Connect Auto Discovery URL: https://authentik.company/application/o/gitea-slug/.well-known/openid-configuration


(./gitea1.png)

`Add Authentication Source` and you should be done. Your Gitea login page should now have a `Sign in With` followed by the authentik logo which you can click on to sign-in to Gitea with Authentik creds.




### Step 4 (Optional)



:::note
In some cases (depending on your setup) GitTea might throw HTTP 500 Errors when doing OIDC authentication trough Auhtentik.
If this is the case, keep on reading.
:::



__Symptoms__


Gitea's log will show an error to the likes of:

`auth.go:638:SignInOAuthCallback() [E] CreateUser: OAuth2 Provider Authentik returned empty or missing fields: [email nickname]`

This can be resolved by creating our own Property mapping in Authentik and instructing Gitea to request that mapping through OIDC.


__Resolution__


Firstly, in Authentik navigate to: _Customisation -> Property Mappings._ Then click `Create` -> _Scope Mapping_

There you'll enter the following information:

- Name: `OAuth2 Gitea Mapping`
- Scope Name: `gitea`
- Description: `Gitea requires your basic profile information and e-mail address.`
- Expression:

```
return {
    "name": request.user.name,
    "given_name": request.user.name,
    "family_name": "",
    "preferred_username": request.user.username,
    "nickname": request.user.username,
    "groups": [group.name for group in request.user.ak_groups.all()],
    "email": request.user.email,
    "email_verified": True
}
```

Then navigate to _Applications -> Providers_ and edit your Gitea Provider.

Under _Advanced Protocol Settings -> Scope_ select:

- Authentik default OAuth mapping: OpenID 'openid'
- OAuth2 Gitea Mapping

Save your changes.

Then, in your Gitea's `app.ini` file:

- If it doesn't exist yet, create a `[oauth2_client]` section
- Set `OPENID_CONNECT_SCOPES` to `gitea` 


Restart Gitea and you should be done!


![]
