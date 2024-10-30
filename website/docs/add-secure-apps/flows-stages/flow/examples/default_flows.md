---
title: Default flows
---

When you create a new provider, you can select certain default flows that will be used with the provider and its associated application. For example, you can select the `default-authentication-flow` (Welcome to authentik!) flow to be presented to all users logging in and authenticating with this provider and application. (You can of course also [create a custom flow](../index.md#create-a-custom-flow))

If no default flow is selected when the provider is created, to determine which flow should be used authentik will first check if there is a default flow configured in the active [**Brand**](../../../customize/brands.md). If no default is configured there, then the policies in all flows with the matching designation are checked, and the first flow with matching policies sorted by `slug` will be used.

import Defaultflowlist from "../../flow/flow_list/\_defaultflowlist.mdx";

<Defaultflowlist />

## nothing beyond this

-   **Authentication flow**: the flow used to authenticate users.
-   **Recovery flow**: If set, allows users to recover their credentials.
-   **Unenrollment flow**: If set, users are able to unenroll themselves. If no flow is set, option is not shown.
-   **User settings flow**: If set, users are able to configure details of their profile.
-   **Device code flow**:

Others:

-   **Authorization flow**: this is defined per provider, when the provider is created, to state whether implicit or explicit authorization is required.

The **Invalidation flow** is a commonly used flow that is not defined by the instance's Brand. This flow is required for OIDC, SAML, Proxy, and RAC providers. Admins can configure this flow to present users log-off options such as "log out of the app but remain logged in to authentik" or "return to the **My Applications** page", or "log out completely". Additionally, admins can apply a custom background image to the prompt box.
