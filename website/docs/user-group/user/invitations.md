---
title: Invitations
description: "Learn how to create an invitation URL for new users to enroll."
---

Invitations are another way to create a user, by inviting someone to join your authentik instnce, as a new user.

With invitations, you can either send a URL to one or more specific recipients, or you can send a URL to a group of users who can then log in and define their credentials.

---
info
You can also create a policy to see if the invitation was ever used.

---

## Create an invitation

Invitations are yet another way to connect Flows, Stages, and Prompts in order to create a speficic user task or worflow.

The fastest way to create an invitation is to use our pre-defined `default-enrollment-flow` that has the necessary stages and prompts already included.

**Step 1. Download the `default-enrollment-flow` file**

Right-click this link for the [`default-enrollment-flow`](/blueprints/example/flows-enrollment-2-stage.yaml) and save the file. For more details, refer to the [documentation](https://goauthentik.io/docs/flow/examples/flows#enrollment-2-stage.

**Step 2. Import the `default-enrollment-flow` file**

In authentik, navigate to the Admin UI, then to Flows and click **Import**. Select the `flows-enrollment-2-stage.yaml` file that you just downloaded.

**Step 3. Create the invitation object**

In the Admin UI, navigate to **Directory --> Invitations**, and then click **Create** to open the **Create Invitation** modal. Define the following fields:
-   **Name**: provide a name for your invitation object.
-   **Expires**: select a date for when you want the invitation to expire.
-   **Flow**: in the drop-down menu, select the **default-enrollment-flow** Flow.
-   **Attributes**: (_optional_) enter [user attributes](./user_attributes.md) here, if you want to pre-define any information about the user that you will invite to enroll.

![Create an invitation modal box](./create_invite.png)

-   **Single use**: specify whether or not you want the invitation to expire after a single use.
