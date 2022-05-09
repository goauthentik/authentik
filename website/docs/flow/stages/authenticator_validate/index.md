---
title: Authenticator Validation Stage
---

This stage validates an already configured Authenticator Device. This device has to be configured using any of the other authenticator stages:

-   [Duo authenticator stage](../authenticator_duo/)
-   [SMS authenticator stage](../authenticator_sms/).
-   [Static authenticator stage](../authenticator_static/).
-   [TOTP authenticator stage](../authenticator_totp/)
-   [WebAuth authenticator stage](../authenticator_webauthn/).

You can select which type of device classes are allowed.

Using the `Not configured action`, you can choose what happens when a user does not have any matching devices.

-   Skip: Validation is skipped and the flow continues
-   Deny: Access is denied, the flow execution ends
-   Configure: This option requires a _Configuration stage_ to be set. The validation stage will be marked as successful, and the configuration stage will be injected into the flow.

## Passwordless authentication

:::info
Requires authentik 2021.12.4
:::

Passwordless authentication currently only supports WebAuthn devices, like security keys and biometrics.

To configure passwordless authentication, create a new Flow with the delegation set to _Authentication_.

As first stage, add an _Authentication validation_ stage, with the WebAuthn device class allowed.
After this stage you can bind any additional verification stages.
As final stage, bind a _User login_ stage.

Users can either access this flow directly via it's URL, or you can modify any Identification stage to add a direct link to this flow.

#### Logging

Logins which used Passwordless authentication have the _auth_method_ context variable set to `auth_webauthn_pwl`, and the device used is saved in the arguments. Example:

```json
{
    "auth_method": "auth_webauthn_pwl",
    "http_request": {
        "args": {
            "query": ""
        },
        "path": "/api/v3/flows/executor/test/",
        "method": "GET"
    },
    "auth_method_args": {
        "device": {
            "pk": 1,
            "app": "authentik_stages_authenticator_webauthn",
            "name": "test device",
            "model_name": "webauthndevice"
        }
    }
}
```
