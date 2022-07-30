---
title: Password stage
---

This is a generic password prompt which authenticates the current `pending_user`. This stage allows the selection of the source the user is authenticated against.

## Passwordless login

To achieve a "passwordless" experience; authenticating users based only on TOTP/WebAuthn/Duo, create an expression policy and optionally skip the password stage.

Depending on what kind of device you want to require the user to have:

#### WebAuthn

```python
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
return WebAuthnDevice.objects.filter(user=request.user, confirmed=True).exists()
```

#### Duo

```python
from authentik.stages.authenticator_duo.models import DuoDevice
return DuoDevice.objects.filter(user=request.user, confirmed=True).exists()
```

Afterwards, bind the policy you've created to the stage binding of the password stage.

Make sure to uncheck _Evaluate on plan_ and check _Re-evaluate policies_, otherwise an invalid result will be cached.
