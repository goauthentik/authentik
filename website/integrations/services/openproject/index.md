---
title: OpenProject
---

<span class="badge badge--secondary">Support level: Community</span>

## What is OpenProject

> OpenProject is a open source project management software.
>
> -- https://www.openproject.org/

## Preparation

The following placeholders will be used:

-   `openproject.company` is the FQDN of the Service install. (Remove this for SaaS)
-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

Create a [OAuth2/OpenID provider](https://goauthentik.io/docs/providers/oauth2) with the following parameters:

-   Client Type: `Confidential`
-   Scopes: `openid`, `email` and `profile`
-   Signing Key: Select any available key
-   Redirect URIs: `https://openproject.company/auth/authentik/callback`

Note the `Client ID` and `Client Secret` values.
Create an [application](https://goauthentik.io/docs/applications), using the provider you've created above and set a slug.
In this example and the following configuration files, the slug `openproject` is used.

### Add family name
OpenProject uses `First name` and `Last name` but Authentik does only provide a name by default (e.g. name="foo bar" instead first_name="foo", last_name="bar"), you can modify the `authentik default OAuth Mapping: OpenID 'profile'` to provide first and last name.
To do that, you need to:
-   log in as `admin`
-   open the `admin interface`
-   navigate to `Customisation` -> `Property Mappings`
-   uncheck `Hide managed mappings`
-   edit the `authentik default OAuth Mapping: OpenID 'profile'` mapping
- add the following lines:
   ```
    "family_name": request.user.name.rsplit(" ", 1)[-1],
    "given_name": request.user.name.rsplit(" ", 1)[0],
   ```

Now, the fields for first and last name will get properly set in OpenProject.


## OpenProject Configuration

OpenProject can be installed in different ways (see the [documentation](https://www.openproject.org/docs/installation-and-operations/installation/)).
For this configuration, the [docker-based installation using docker-compose](https://www.openproject.org/docs/installation-and-operations/configuration/#docker) is used.


As described in the [installation guide](https://www.openproject.org/docs/installation-and-operations/installation/docker/#quick-start), the first step is to clone the [openproject-deploy repository](https://github.com/opf/openproject-deploy/tree/stable/13/compose).
Following the [instructions of the openproject-deploy repository](https://github.com/opf/openproject-deploy/tree/stable/13/compose#openproject-installation-with-docker-compose), create a copy of the provided `.env.example` and adjust its content:
-   Set `OPENPROJECT_HOST__NAME` to `openproject.company`

The next step is to add some more configuration lines to the `.env` file:

```
# sso auth
OPENPROJECT_OMNIAUTH__DIRECT__LOGIN__PROVIDER="Authentik"

# The name of the login button in OpenProject, you can freely set this to anything you like
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_DISPLAY__NAME="Authentik"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_HOST="authentik.company"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_IDENTIFIER="< insert the `Client ID` you have copied in the authentik configuration step >"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_SECRET="< insert the `Client Secret` you have copied in the authentik configuration step >"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_ISSUER="https://authentik.company"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_AUTHORIZATION__ENDPOINT="https://authentik.company/application/o/authorize/"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_TOKEN__ENDPOINT="https://authentik.company/application/o/token/"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_USERINFO__ENDPOINT="https://authentik.company/application/o/userinfo/"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_END__SESSION__ENDPOINT="https://authentik.company/application/o/openproject/end-session/"
OPENPROJECT_OPENID__CONNECT_AUTHENTIK_ATTRIBUTE__MAP_LOGIN="preferred_username"
```

Complete the rest of the installation following the installation instructions of the OpenProject documentation.

### Disable password login

If you want to disable the traditional password login for the OpenProject instance, you need to add the lines to the `.env` file:

```
OPENPROJECT_DISABLE__PASSWORD__LOGIN=true
OPENPROJECT_SELF__REGISTRATION=disabled
```

For more information regarding environment variables, read the [environment variables documentation](https://www.openproject.org/docs/installation-and-operations/configuration/environment/).

