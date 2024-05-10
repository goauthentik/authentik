---
title: Add an Entra ID provider
---

<span class="badge badge--primary">Enterprise</span>

---

The Entra ID provider ... words here... s

:::info
This feature is in technical preview, so please report any bugs on [GitHub](https://github.com/goauthentik/authentik/issues).
:::

For more information about using a Entra ID provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create a Google Worksapce provider provider in authentik, you must have already [configured Entra ID](./setup-entra.md) to integrate with authentik.

:::info
When adding the Entra ID provider in authentik, you must define the **Backchannel provider** using the name of the Entra ID provider that you created in authentik. Do NOT add any value in the **Provider** field (doing so will cause the provider to display as an application on the user interface, under **My apps**, which is not supported for Entra ID).
:::

### Create the Entra ID provider in authentik

1. Log in as an admin to authentik, and go to the Admin interface.

2. In the Admin interface, navigate to **Applications -> Providers**.

3. Click **Create**, and in the **New provider** modal box, define the following fields:
*   **Name**: define a descriptive name, such as "Entra provider".
** Protocol settings**:
*   **Client ID**: enter the Client ID that you [copied from your Entra app](./setup-entra.md).
*   **Client Secret**: Enter the secret from Entra.
*   **Tenant ID**: enter the Tenat ID from Entra.


### Create an Entra ID app in authentik
