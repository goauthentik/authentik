---
title: GitLab
---

<span class="badge badge--primary">Support level: authentik</span>

## What is GitLab

From https://about.gitlab.com/what-is-gitlab/

:::note
GitLab is a complete DevOps platform, delivered as a single application. This makes GitLab unique and makes Concurrent DevOps possible, unlocking your organization from the constraints of a pieced together toolchain. Join us for a live Q&A to learn how GitLab can give you unmatched visibility and higher levels of efficiency in a single application across the DevOps lifecycle.
:::

## Preparation

The following placeholders will be used:

-   `gitlab.company` is the FQDN of the GitLab Install
-   `authentik.company` is the FQDN of the authentik Install

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

-   ACS URL: `https://gitlab.company/users/auth/saml/callback`
-   Audience: `https://gitlab.company`
-   Issuer: `https://gitlab.company`
-   Binding: `Redirect`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.

## GitLab Configuration

Paste the following block in your `gitlab.rb` file, after replacing the placeholder values from above. The file is located in `/etc/gitlab`.
To get the value for `idp_cert_fingerprint`, go to the Certificate list under _Identity & Cryptography_, and expand the selected certificate.

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
      idp_sso_target_url: 'https://authentik.company/application/saml/<authentik application slug>/sso/binding/redirect/',
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
