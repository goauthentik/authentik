---
title: Password stage
---

This is a generic password prompt which authenticates the current `pending_user`. This stage allows the selection of the source the user is authenticated against.

## Passwordless login

There are two different ways to configure passwordless authentication; you can follow the instructions [here](../authenticator_validate/index.md#passwordless-authentication) to allow users to directly authenticate with their authenticator (only supported for WebAuthn devices), or dynamically skip the password stage depending on the users device, which is documented here.

Depending on what kind of device you want to require the user to have:

#### WebAuthn

```python
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
return WebAuthnDevice.objects.filter(user=request.context['pending_user'], confirmed=True).exists()
```

#### Duo

```python
from authentik.stages.authenticator_duo.models import DuoDevice
return DuoDevice.objects.filter(user=request.context['pending_user'], confirmed=True).exists()
```

Afterwards, bind the policy you've created to the stage binding of the password stage.

Make sure to uncheck _Evaluate when flow is planned_ and check _Evaluate when stage is run_, otherwise an invalid result will be cached.
