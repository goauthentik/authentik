---
title: SMS Authenticator Setup stage
---

This stage configures an SMS-based authenticator using either Twilio, or a generic HTTP endpoint.

## Providers

#### Twilio

Navigate to https://console.twilio.com/, and log in to your existing account, or create a new one.

In the sidebar, navigate to _Explore Products_, then _Messaging_, and _Services_ below that.

Click on _Create Messaging Service_ to create a new set of API credentials.

Give the service a Name, and select _Verify users_ as a use-case.

In the next step, add an address from your Sender Pool. Instructions on how to create numbers are not covered here, please check the Twilio documentation [here](https://www.twilio.com/docs).

The other two steps can be skipped using the _Skip setup_ button.

Navigate back to the root of your Twilio console, and copy the Auth token. This is the value for the _Twilio Auth Token_ field in authentik. Copy the value of **Account SID**. This is the value for the _Twilio Account SID_ field in authentik.

#### Generic

For the generic provider, a POST request will be sent to the URL you have specified in the _External API URL_ field. The request payload looks like this

```json
{
    "From": "<value of the *From number* field>",
    "To": "<the phone number of the user's device>",
    "Body": "<the token that the user needs to authenticate>,
}
```

Authentication can either be done as HTTP Basic, or via a Bearer Token. Any response with status 400 or above is counted as failed, and will prevent the user from proceeding.

Starting with authentik 2022.10, a custom webhook mapping can be specified to freely customize the payload of the request. For example:

```python
return {
    "from": stage.from_number,
    "to": device.phone_number,
    "body": f"foo bar baz {token}".
}
```

## Verify only <span class="badge badge--version">authentik 2022.6+</span>

To only verify the validity of a users' phone number, without saving it in an easily accessible way, you can enable this option. Phone numbers from devices enrolled through this stage will only have their hashed phone number saved. These devices can also not be used with the [Authenticator validation](../authenticator_validate/index.md) stage.

## Limiting phone numbers

To limit phone numbers (for example to a specific region code), you can create an expression policy to validate the phone number, and use a prompt stage for input.

### Expression policy

Create an expression policy to check the phone number:

```python
# Trim all whitespace in and around the user input
phone_number = regex_replace(request.context["prompt_data"]["phone"], r'\s+', '')

# Only allow a specific region code
if phone_number.startswith("+1234"):
    return True
ak_message("Invalid phone number or missing region code")
return False
```

### Prompt stage

Create a text prompt field with the _field key_ set to `phone`. Make sure it is selected as a required field.

Create a prompt stage with the phone field you created above, and select the expression policy created above as validation policy.

### Flow

Create a new flow to enroll SMS devices. Bind the prompt stage created above as first stage, and create/bind a _SMS Authenticator Setup Stage_, and bind it to the flow as second stage. This stage will see the `phone` field in the flow's context's `prompt_data`, and not prompt the user for a phone number.
