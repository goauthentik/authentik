---
title: Duo Authenticator Setup stage
---

This stage configures a Duo authenticator. To get the API Credentials for this stage, open your Duo Admin dashboard.

Go to Applications, click on Protect an Application and search for "Auth API". Click on Protect.

Copy all of the integration key, secret key and API hostname, and paste them in the Stage form.

Devices created reference the stage they were created with, since the API credentials are needed to authenticate. This also means when the stage is deleted, all devices are removed.

## Importing users <span class="badge badge--version">authentik 2022.9+</span>

:::info
Due to the way the Duo API works, authentik can only automatically import existing Duo users when a Duo MFA or higher license is active.
:::

To import a device, open the Stages list in the authentik Admin interface. On the right next to the import button you'll see an import button, with which you can import Duo devices to authentik users.

The Duo username can be found by navigating to your Duo Admin dashboard and selecting _Users_ in the sidebar. Optionally if you have multiple users with the same username, you can click on a User and copy their ID from the URL, and use that to import the device.

### Older versions <span class="badge badge--version">authentik 2021.9.1+</span>

You can call the `/api/v3/stages/authenticator/duo/{stage_uuid}/import_devices/` endpoint ([see here](https://goauthentik.io/api/#post-/stages/authenticator/duo/-stage_uuid-/import_devices/)) using the following parameters:

- `duo_user_id`: The Duo User's ID. This can be found in the Duo Admin Portal, navigating to the user list and clicking on a single user. Their ID is shown in th URL.
- `username`: The authentik user's username to assign the device to.

Additionally, you need to pass `stage_uuid` which is the `authenticator_duo` stage, in which you entered your API credentials.
