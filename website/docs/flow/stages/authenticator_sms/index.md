---
title: SMS authenticator setup stage
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

Afterwards, copy the value of **Messaging Service SID**. This is the value for the _Twilio Account SID_ field in authentik.

Navigate back to the root of your Twilio console, and copy the Auth token. This is the value for the _Twilio Auth Token_ field in authentik.

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

## Verify only

:::info
Requires authentik 2022.6
:::

To only verify the validity of a users' phone number, without saving it in an easily accessible way, you can enable this option. Phone numbers from devices enrolled through this stage will only have their hashed phone number saved. These devices can also not be used with the [Authenticator validation](../authenticator_validate/) stage.
