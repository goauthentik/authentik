---
title: Consent stage
---

The Consent stage asks the user to approve sharing data with an application or relying party.

## Overview

This stage is commonly used in authorization flows, where a user should explicitly consent before authentik shares profile data or other claims with an application.

The default `default-provider-authorization-explicit-consent` flow already includes a Consent stage.

A typical use case is prompting the user to allow authentik to share profile data such as name, email address, or avatar with the application they are signing in to.

## Configuration options

- **Mode**: control how long a granted consent remains valid.
    - **Always require consent**: prompt every time.
    - **Consent given lasts indefinitely**: store consent without expiration.
    - **Consent expires**: store consent until the configured expiry time.
- **Consent expires in**: expiration offset used when the mode is set to expiring consent.

## Flow integration

Bind this stage into an authorization flow anywhere the user should see the consent prompt.

If you use the default explicit-consent authorization flow, the stage is already present and usually does not need to be added manually.

## Notes

### Default flow

If you are using the default `default-provider-authorization-explicit-consent` flow, you usually do not need to add a Consent stage manually because it is already present.

If you are building a custom authorization flow, the usual sequence is:

1. Create the Consent stage.
2. Bind it into the authorization flow.
3. Optionally bind an expression policy to the stage binding if the consent text should be customized.

If you are adding the stage from scratch in the Admin interface, the typical workflow is:

1. Go to **Flows and Stages** > **Stages** and create a **Consent Stage**.
2. Set the **Mode** and, if needed, the expiry duration.
3. Open the target authorization flow.
4. Add the Consent stage to that flow's stage bindings.

### Custom consent text

You can customize the text shown on the consent screen by setting the `consent_header` key in flow context before the stage runs, for example from an expression policy:

```python
request.context["flow_plan"].context["consent_header"] = (
    "Are you OK with your IdP provider sharing your user identification data "
    "with the application?"
)
return True
```

Bind that policy to the Consent stage binding inside the authorization flow where you want the wording to change.

The binding workflow is:

1. Open the authorization flow that contains the Consent stage.
2. Go to **Stage Bindings**.
3. Expand the Consent stage binding that should use the custom text.
4. Bind the expression policy to that stage binding.

### Stored consent

When consent is stored, authentik keeps track of the user, the application, and the granted permissions so later requests can reuse or re-prompt according to the selected mode.
