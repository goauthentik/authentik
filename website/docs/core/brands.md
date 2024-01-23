---
title: Brands
slug: /brands
---

authentik support soft multi-tenancy. This means that you can configure several options depending on domain, but all the objects like applications, providers, etc, are still global. This can be handy to use the same authentik instance, but branded differently for different domains.

The main settings that brands influence are flows and branding.

## Flows

authentik picks a default flow by picking the flow that is selected in the current brand, otherwise any flow that

    - matches the required designation
    - comes first sorted by slug
    - is allowed by policies

This means that if you want to select a default flow based on policy, you can just leave the brand default empty.

## Branding

The brand can configure the branding title (shown in website document title and several other places), and the sidebar/header logo.
