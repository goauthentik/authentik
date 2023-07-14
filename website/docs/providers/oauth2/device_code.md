# Device code flow

(Also known as device flow and [RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628))

This type of authentication flow is useful for devices with limited input abilities and/or devices without browsers.

### Requirements

This device flow is only possible if the active tenant has a device code flow setup. This device code flow is run _after_ the user logs in, and before the user authenticates.

authentik doesn't ship with a default flow for this usecase, so it is recommended to create a new flow for this usecase with the designation of _Stage configuration_

### Device-side

The flow is initiated by sending a POST request to the device authorization endpoint, `/application/o/device/` with the following contents:

```
POST /application/o/device/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

client_id=application_client_id&
scopes=openid email my-other-scope
```

The response contains the following fields:

-   `device_code`: Device code, which is the code kept on the device
-   `verification_uri`: The URL to be shown to the enduser to input the code
-   `verification_uri_complete`: The same URL as above except the code will be prefilled
-   `user_code`: The raw code for the enduser to input
-   `expires_in`: The total seconds after which this token will expire
-   `interval`: The interval in seconds for how often the device should check the token status

---

With this response, the device can start checking the status of the token by sending requests to the token endpoint like this:

```
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code&
client_id=application_client_id&
device_code=device_code_from_above
```

If the user has not opened the link above yet, or has not finished the authentication and authorization yet, the response will contain an `error` element set to `authorization_pending`. The device should re-send the request in the interval set above.

If the user _has_ finished the authentication and authorization, the response will be similar to any other generic OAuth2 Token request, containing `access_token` and `id_token`.
