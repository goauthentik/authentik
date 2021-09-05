---
title: Automated install
---

To install authentik automatically (skipping the Out-of-box experience), you can use the following environment variables:

### `AK_ADMIN_PASS`

Configure the default password for the `akadmin` user. Only read on the first startup. Can be used for any flow executor.

### `AK_ADMIN_TOKEN`

:::note
This option has been added in 2021.8
:::

Create a token for the default `akadmin` user. Only read on the first startup. The string you specify for this variable is the token key you can use to authenticate yourself to the API.
