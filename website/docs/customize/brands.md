---
title: Brands
slug: /brands
---

You can configure several differently "branded" options depending on the associated domain, even though objects such as applications, providers, etc, are still global. This can be handy to use the same authentik instance, but branded differently for different domains.

The main settings that brands influence are flows and branding.

## Flows

You can explicitly select, in your instance's Brand settings, the _default flows_ to use for the current brand. To do so, log in as an administrator, open the Admin interface, and navigate to **System -> Brands**. There you can optionally configure these default flows:

- Authentication flow: the flow used to authenticate users. If left empty, the first applicable flow sorted by the slug is used.
- Invalidation flow: for typical use cases, select the `default-invalidation-flow` (Logout) flow. This flow logs the user out of authentik when the application session ends (user logs out of the app).
- Recovery flow: if set, the user can access an option to recover their login credentials.
- Unenrollment flow: if set, users are able to unenroll themselves using this flow. If no flow is set, option is not shown.
- User settings flow: if set, users are able to configure details of their profile.
- Device code flow: if set, the OAuth Device Code profile can be used, and the selected flow will be used to enter the code.

If a default flow is _not_ set in the brand, then authentik selects any flow that:

    - matches the required designation
    - comes first sorted by slug
    - is allowed by policies

This means that if you want to select a default flow based on policy, you can leave the brand default empty. To learn more about default flows, refer to our [documentation](../add-secure-apps/flows-stages/flow/examples/default_flows.md).

## Branding

The brand configuration controls the branding title (shown in website document title and several other places), the sidebar/header logo that appears in the upper left of the product interface, and the favicon on a browser tab.

:::info
Starting with authentik 2024.6.2, the placeholder `%(theme)s` can be used in the logo configuration option, which will be replaced with the active theme.
:::

## External user settings

You can configure authentik to redirect external users to a default application when they successfully authenticate (without being sent from a specific application). To do so, use the **Default application** configuration on the **System -> Brands** page of the Admin interface.
