---
title: Example
---

This is one of the default packaged blueprints to create the default authentication flow.

<!-- prettier-ignore-start -->
```yaml
version: 1
metadata:
    name: Default - Authentication flow
entries:
    # Order of entries is important when using !KeyOf, as tags are evaluated in order they are in
    # the document
    - attrs:
          # Only options that are required should be set here. Default values should not be stated
          # here, as they will prevent anyone from overwriting the value
          designation: authentication
          name: Welcome to authentik!
          title: Welcome to authentik!
      identifiers:
          slug: default-authentication-flow
      model: authentik_flows.flow
      id: flow
    - attrs:
          configure_flow:
              !Find [authentik_flows.flow, [slug, default-password-change]]
      identifiers:
          name: default-authentication-password
      id: default-authentication-password
      model: authentik_stages_password.passwordstage
    - identifiers:
          name: default-authentication-mfa-validation
      # If we're fine with all defaults, `attrs` can be omitted
      id: default-authentication-mfa-validation
      model: authentik_stages_authenticator_validate.authenticatorvalidatestage
    - identifiers:
          name: default-authentication-identification
      id: default-authentication-identification
      model: authentik_stages_identification.identificationstage
    - attrs:
          session_duration: seconds=0
      identifiers:
          name: default-authentication-login
      id: default-authentication-login
      model: authentik_stages_user_login.userloginstage
    - identifiers:
          order: 10
          stage: !KeyOf default-authentication-identification
          target: !KeyOf flow
      model: authentik_flows.flowstagebinding
    - identifiers:
          order: 20
          stage: !KeyOf default-authentication-password
          target: !KeyOf flow
      model: authentik_flows.flowstagebinding
    - identifiers:
          order: 30
          stage: !KeyOf default-authentication-mfa-validation
          target: !KeyOf flow
      model: authentik_flows.flowstagebinding
    - identifiers:
          order: 100
          stage: !KeyOf default-authentication-login
          target: !KeyOf flow
      model: authentik_flows.flowstagebinding
```
<!-- prettier-ignore-end -->
