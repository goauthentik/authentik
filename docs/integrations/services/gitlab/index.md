# GitLab Integration

## What is GitLab

From https://about.gitlab.com/what-is-gitlab/

!!! note ""
    GitLab is a complete DevOps platform, delivered as a single application. This makes GitLab unique and makes Concurrent DevOps possible, unlocking your organization from the constraints of a pieced together toolchain. Join us for a live Q&A to learn how GitLab can give you unmatched visibility and higher levels of efficiency in a single application across the DevOps lifecycle.

## Preparation

The following placeholders will be used:

-   `gitlab.company` is the FQDN of the GitLab Install
-   `passbook.company` is the FQDN of the passbook Install

Create an application in passbook and note the slug, as this will be used later. Create a SAML Provider with the following Parameters:

-   ACS URL: `https://gitlab.company/users/auth/saml/callback`
-   Audience: `https://gitlab.company`
-   Issuer: `https://gitlab.company`

You can of course use a custom Signing Certificate, and adjust the Assertion Length. To get the value for `idp_cert_fingerprint`, you can use a tool like [this](https://www.samltool.com/fingerprint.php).

## GitLab Configuration

Paste the following block in your `gitlab.rb` file, after replacing the placeholder values from above. The file is located in `/etc/gitlab`.

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
      idp_cert_fingerprint: '4E:1E:CD:67:4A:67:5A:E9:6A:D0:3C:E6:DD:7A:F2:44:2E:76:00:6A',
      idp_sso_target_url: 'https://passbook.company/application/saml/<passbook application slug>/login/',
      issuer: 'https://gitlab.company',
      name_identifier_format: 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
      attribute_statements: {
        email: ['urn:oid:1.3.6.1.4.1.5923.1.1.1.6'],
        first_name: ['urn:oid:2.5.4.3'],
        nickname: ['urn:oid:2.16.840.1.113730.3.1.241']
      }
    },
    label: 'passbook'
  }
]
```

Afterwards, either run `gitlab-ctl reconfigure` if you're running GitLab Omnibus, or restart the container if you're using the container.
