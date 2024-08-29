---
title: Brands
slug: /brands
---

You can configure several differently "branded" options depending on the associated domain, even though objects such as applications, providers, etc, are still global. This can be handy to use the same authentik instance, but branded differently for different domains.

The main settings that brands influence are flows and branding.

## Flows

authentik picks a default flow by selecting the flow that is configured in the current brand, otherwise any flow that:

    - matches the required designation
    - comes first sorted by slug
    - is allowed by policies

This means that if you want to select a default flow based on policy, you can leave the brand default empty.

## Branding

The brand configuration controls the branding title (shown in website document title and several other places), the sidebar/header logo that appears in the upper left of the product interface, and the favicon on a browser tab.

:::info
Starting with authentik 2024.6.2, the placeholder `%(theme)s` can be used in the logo configuration option, which will be replaced with the active theme.
:::

## External user settings

You can use the **Default application** configuration on the **System -> Brands** page of the Admin interface to redirect external users to a default application when they successfully authenticate without being sent from a specific application.
