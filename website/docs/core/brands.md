---
title: Brands
slug: /brands
---

You can configure several differently "branded" options depending on the associated domain, even though objects such as applications, providers, etc, are still global. This can be handy to use the same authentik instance, but branded differently for different domains.

The main settings that brands influence are flows and branding.

## Flows

authentik picks a default flow by picking the flow that is selected in the current brand, otherwise any flow that

    - matches the required designation
    - comes first sorted by slug
    - is allowed by policies

This means that if you want to select a default flow based on policy, you can leave the brand default empty.

## Branding

The brand configuration controls the branding title (shown in website document title and several other places), and the sidebar/header logo that appears in the upper left of the product interface.
