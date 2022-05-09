---
title: SMS authenticator setup stage
---

This stage configures an SMS-based authenticator using either Twilio, or a generic HTTP endpoint.

## Twilio

Navigate to https://console.twilio.com/, and log in to your existing account, or create a new one.

In the sidebar, navigate to _Explore Products_, then _Messaging_, and _Services_ below that.

Click on _Create Messaging Service_ to create a new set of API credentials.

Give the service a Name, and select _Verify users_ as a use-case.

In the next step, add an address from your Sender Pool. Instructions on how to create numbers are not covered here, please check the Twilio documentation [here](https://www.twilio.com/docs).

The other two steps can be skipped using the _Skip setup_ button.

Afterwards, copy the value of **Messaging Service SID**. This is the value for the _Twilio Account SID_ field in authentik.

Navigate back to the root of your Twilio console, and copy the Auth token. This is the value for the _Twilio Auth Token_ field in authentik.

## Generic

For the generic provider, a POST request will be sent to the URL you have specified in the _External API URL_ field. The request payload looks like this

```json
{
    "From": "<value of the *From number* field>",
    "To": "<the phone number of the user's device>",
    "Body": "<the token that the user needs to authenticate>,
}
```

Authentication can either be done as HTTP Basic, or via a Bearer Token. Any response with status 400 or above is counted as failed, and will prevent the user from proceeding.
