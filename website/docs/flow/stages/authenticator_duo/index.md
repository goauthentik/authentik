---
title: Duo authenticator setup stage
---

This stage configures a Duo authenticator. To get the API Credentials for this stage, open your Duo Admin dashboard.

Go to Applications, click on Protect an Application and search for "Auth API". Click on Protect.

Copy all of the integration key, secret key and API hostname, and paste them in the Stage form.

Devices created reference the stage they were created with, since the API credentials are needed to authenticate. This also means when the stage is deleted, all devices are removed.

## Importing users

:::info
Due to the way the Duo API works, authentik cannot automatically import existing Duo users.
:::

:::info
This API requires version 2021.9.1 or later
:::

You can call the `/api/v3/stages/authenticator/duo/{stage_uuid}/import_devices/` endpoint ([see here](https://goauthentik.io/api/#post-/stages/authenticator/duo/-stage_uuid-/import_devices/)) using the following parameters:

-   `duo_user_id`: The Duo User's ID. This can be found in the Duo Admin Portal, navigating to the user list and clicking on a single user. Their ID is shown in th URL.
-   `username`: The authentik user's username to assign the device to.

Additionally, you need to pass `stage_uuid` which is the `authenticator_duo` stage, in which you entered your API credentials.
