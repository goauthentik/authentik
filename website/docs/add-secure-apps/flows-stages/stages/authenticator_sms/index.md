---
title: SMS authenticator setup stage
---

The SMS Authenticator Setup stage enrolls an SMS-based authenticator for the current user by using either Twilio or a generic HTTP endpoint.

## Overview

This stage stores a phone number, enabling one-time codes to be sent via SMS.

In normal mode, the enrolled phone number can later be used with the [Authenticator Validation stage](../authenticator_validate/index.md). In **verify only** mode, the stage only verifies ownership of a phone number during enrollment and stores a hash instead of the number itself.

## Configuration options

- **Provider**: choose either **Twilio** or **Generic**.
- **From number**: sender number or identifier used for outbound SMS.
- **Account SID / External API URL**: for Twilio this is the account SID; for the generic provider this is the target API URL.
- **Auth / token**: for Twilio this is the auth token; for the generic provider this is the bearer token or basic-auth username.
- **Auth password**: optional password for generic basic authentication.
- **Auth type**: choose **Basic** or **Bearer** authentication for the generic provider.
- **Verify only**: verify phone ownership during enrollment without storing the plain phone number for later MFA use.
- **Mapping**: optional webhook mapping used to customize the payload sent to custom providers.
- **Authenticator type name**: optional friendly name shown to the user in self-service settings.
- **Configuration flow**: optional authenticated flow that lets users enroll this authenticator from user settings.

## Flow integration

Use this stage in an enrollment or user-settings flow where the user should add an SMS authenticator.

To require SMS during login, add an [Authenticator Validation stage](../authenticator_validate/index.md) to the authentication flow and allow the **SMS** device class.

If you enable **Verify only**, devices enrolled through this stage cannot be used by the Authenticator Validation stage.

## Notes

### Twilio

For the Twilio provider, create a messaging service and collect the **Account SID**, **Auth token**, and a usable sender number from the Twilio console.

A typical Twilio setup looks like this:

1. Log in to the Twilio console.
2. Go to **Explore Products** > **Messaging** > **Services**.
3. Create a new messaging service and choose a verification-oriented use case.
4. Add a sender from the service's sender pool.
5. Copy the **Account SID** and **Auth token** into the stage configuration.

Using a property mapping, you can customize the message sent via Twilio. The mapping should return a dictionary with a `message` key. For example:

```python
return {
    "message": f"This is a custom message for {request.http_request.brand.branding_title} SMS authentication. The code is {token}."
}
```

Useful variables in that mapping include:

- `device.phone_number`
- `stage.from_number`
- `request.http_request.brand`

### Generic provider

For the generic provider, authentik sends an HTTP `POST` request to the configured API URL. The default payload contains:

```json
{
    "From": "<value of the From number field>",
    "To": "<the phone number of the user's device>",
    "Body": "<the token that the user needs to authenticate>",
    "Message": "<the full SMS message>"
}
```

Any response with status `400` or higher is treated as a failed send and blocks the user from proceeding.

You can also customize the generic-provider payload with a webhook mapping. For example:

```python
return {
    "from": stage.from_number,
    "to": device.phone_number,
    "body": f"foo bar baz {token}",
}
```

### Limiting phone numbers

To control which phone numbers are accepted, collect the number in a [Prompt stage](../prompt/index.md) and validate it with an expression policy before this stage runs. If a prompt field uses the key `phone`, the SMS setup stage will read that value from `prompt_data` instead of prompting the user again.

Example expression policy:

```python
phone_number = regex_replace(request.context["prompt_data"]["phone"], r"\s+", "")

if phone_number.startswith("+1234"):
    return True
ak_message("Invalid phone number or missing region code")
return False
```

A typical flow for this looks like:

1. Create a required text prompt field with the key `phone`.
2. Create a Prompt stage that contains that field.
3. Bind the validation policy to the Prompt stage.
4. Bind the Prompt stage before the SMS setup stage in the enrollment flow.
