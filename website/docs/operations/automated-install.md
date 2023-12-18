---
title: Automated install
---

To install authentik automatically (skipping the Out-of-box experience), you can use the following environment variables:

### `AUTHENTIK_BOOTSTRAP_PASSWORD`

Configure the default password for the `akadmin` user. Only read on the first startup. Can be used for any flow executor.

### `AUTHENTIK_BOOTSTRAP_TOKEN`

:::note
Requires authentik 2021.8
:::

Create a token for the default `akadmin` user. Only read on the first startup. The string you specify for this variable is the token key you can use to authenticate yourself to the API.

### `AUTHENTIK_BOOTSTRAP_EMAIL`

:::note
Requires authentik 2023.3
:::

Set the email address for the default `akadmin` user.
