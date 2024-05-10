---
title: Create a Google Workspace provider
---

<span class="badge badge--primary">Enterprise</span>

---

:::info
This feature is in technical preview, so please report any bugs on [GitHub](https://github.com/goauthentik/authentik/issues).
:::

The GWS provider ... words here... s

For more information about using a Google Workspace provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create a Google Worksapce provider provider in authentik, you must have already [configured Google Workspace](./setup-gws.md) to integrate with authentik.

:::info
When adding the Google Workspace provider in authentik, you must define the **Backchannel provider** using the name of the Google Workspace provider that you created in authentik. Do NOT add any value in the **Provider** field (doing so will cause the provider to display as an application on the user interface, under **My apps**, which is not supported for Google Workspace).
:::

### Create the Google Workspace provider in authentik

1. Log in as an admin to authentik, and go to the Admin interface.

2. In the Admin interface, navigate to **Applications -> Providers**.

3. Click **Create**. Follow the [instructions](../../applications/manage_apps.md#instructions) to create your Google Workspace provider.
