---
title: Integrate with GitLab
sidebar_label: GitLab
---

# GitLab

<span class="badge badge--primary">Support level: authentik</span>

## What is GitLab

> GitLab is a complete DevOps platform with features for version control, CI/CD, issue tracking, and collaboration, facilitating efficient software development and deployment workflows.
>
> -- https://about.gitlab.com/what-is-gitlab/

:::info
In case something goes wrong with the configuration or you need to log in as admin, you can use the URL `https://gitlab.company/users/sign_in?auto_sign_in=false` to log in using the built-in authentication.
:::

## Authentication

There are 2 ways to configure single sign on (SSO) for GitLab:

- [via SAML](#saml-auth)
- [via OIDC Connect (OAuth)](#openid-connect-auth)

### SAML auth

#### Preparation

The following placeholders are used in this guide:

- `gitlab.company` is the FQDN of the GitLab installation.
- `authentik.company` is the FQDN of the authentik installation.

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

- ACS URL: `https://gitlab.company/users/auth/saml/callback`
- Audience: `https://gitlab.company`
- Issuer: `https://gitlab.company`
- Binding: `Redirect`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

#### GitLab Configuration

Paste the following block in your `/etc/gitlab/gitlab.rb` file, after replacing the placeholder values from above.
To get the value for `idp_cert_fingerprint`, navigate to the authentik Admin interface, expand the **System** section and select **Certificates**. Then, expand the selected certificate and copy the SHA1 Certificate Fingerprint.

```ruby
gitlab_rails['omniauth_enabled'] = true
gitlab_rails['omniauth_allow_single_sign_on'] = ['saml']
gitlab_rails['omniauth_sync_email_from_provider'] = 'saml'
gitlab_rails['omniauth_sync_profile_from_provider'] = ['saml']
gitlab_rails['omniauth_sync_profile_attributes'] = ['email']
gitlab_rails['omniauth_auto_sign_in_with_provider'] = 'saml'
gitlab_rails['omniauth_block_auto_created_users'] = false
gitlab_rails['omniauth_auto_link_saml_user'] = true
gitlab_rails['omniauth_providers'] = [
  {
    name: 'saml',
    args: {
      assertion_consumer_service_url: 'https://gitlab.company/users/auth/saml/callback',
      # Shown when navigating to certificates in authentik
      idp_cert_fingerprint: '4E:1E:CD:67:4A:67:5A:E9:6A:D0:3C:E6:DD:7A:F2:44:2E:76:00:6A',
      idp_sso_target_url: 'https://authentik.company/application/saml/<gitlab application slug>/sso/binding/redirect/',
      issuer: 'https://gitlab.company',
      name_identifier_format: 'urn:oasis:names:tc:SAML:2.0:nameid-format:persistent',
      attribute_statements: {
        email: ['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress'],
        first_name: ['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name'],
        nickname: ['http://schemas.goauthentik.io/2021/02/saml/username']
      }
    },
    label: 'authentik'
  }
]
```

Afterwards, either run `gitlab-ctl reconfigure` if you're running GitLab Omnibus, or restart the container if you're using the container.

### OpenID Connect auth

#### Preparation

The following placeholders are used in this guide:

- `gitlab.company` is the FQDN of the GitLab Install
- `authentik.company` is the FQDN of the authentik Install

Create an application in authentik and note the slug, as this will be used later. Create a OAuth2 Provider with the following parameters:

- Client type: `Confidential`
- Redirect URI/Origins: `https://gitlab.company/users/auth/openid_connect/callback`
- Scopes: `email`, `openid`, `profile`
- Subject mode: `Based on the Users's Email`
- Include claims in id_token: `True`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.

#### GitLab Configuration

Paste the following block in your `/etc/gitlab/gitlab.rb` file, after replacing the placeholder values from above.

```ruby
gitlab_rails['omniauth_allow_single_sign_on'] = ['openid_connect']
gitlab_rails['omniauth_sync_email_from_provider'] = 'openid_connect'
gitlab_rails['omniauth_sync_profile_from_provider'] = ['openid_connect']
gitlab_rails['omniauth_sync_profile_attributes'] = ['email']
gitlab_rails['omniauth_auto_sign_in_with_provider'] = 'openid_connect'
gitlab_rails['omniauth_block_auto_created_users'] = false
gitlab_rails['omniauth_auto_link_saml_user'] = true
gitlab_rails['omniauth_auto_link_user'] = ["openid_connect"]
gitlab_rails['omniauth_providers'] = [
  {
    name: 'openid_connect',
    label: 'My Company OIDC Login',
    args: {
      name: 'openid_connect',
      scope: ['openid','profile','email'],
      response_type: 'code',
      issuer: 'https://authentik.company/application/o/gitlab-slug/',
      discovery: true,
      client_auth_method: 'query',
      uid_field: 'preferred_username',
      send_scope_to_token_endpoint: 'true',
      pkce: true,
      client_options: {
        identifier: '${OIDC_CLIENT_ID}',
        secret: '${OIDC_CLIENT_SECRET}',
        redirect_uri: 'https://gitlab.company/users/auth/openid_connect/callback'
      }
    }
  }
]
```

For further GitLab provider args have a look at the specific GitLab docs at https://docs.gitlab.com/ee/integration/openid_connect_provider.html
