---
title: Invitations
description: "Learn how to create an invitation URL for new users to enroll."
---

Invitations are another way to create a user, by inviting someone to join your authentik instnce, as a new user.

With invitations, you can either send a URL to one or more specific recipients, or you can send a URL to a group of users who can then log in and define their credentials.

--- info
You can also create a policy to see if the invitation was ever used.

---

## Create an invitation

To use an invitation, you will need to connect a Flow, a Stage, and an invitation object... plus some prompts...?

The fastest way to create an invitation is to use our `default-enrollment-flow`... go to Example Flows and select the Enrollment (2 stage) choice... download that file... then go to Flows and click **Import** and navigate to the downloaded file... then...?

OLD TEXT below

Step 1. Create a new Flow (or re-use an existing Flow that was alreadty created for this purpose).... in the Designation filed, you MUST elect Enrollment!!!

Step 2. Create a new Stage, or use an existing one....

Step 3. Create the invitation object... on the Flow field, select the Flow that you created in Step 1.

Youc an enter user attributes here, if you want to pre-define their username, or email address, or user... or leave it blank and the new user can fill it in when they enroll.
