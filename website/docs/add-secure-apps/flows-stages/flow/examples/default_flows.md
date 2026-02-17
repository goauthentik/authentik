---
title: Default flows
---

When you create a new provider, you can select certain default flows that will be used with the provider and its associated application. For example, you can [create a custom flow](../index.md#create-a-custom-flow) that overrides the defaults configured on the brand.

<<<<<<< HEAD
If no default flow is selected when the provider is created, to determine which flow should be used authentik will first check if there is a default flow configured in the active [**Brand**](../../../../sys-mgmt/brands.md). If no default is configured there, authentik will go through all flows with the matching designation, sorted by `slug` and evaluate policies bound directly to the flows, and the first flow whose policies allow access will be picked.
=======
If no default flow is selected when the provider is created, authentik will first check if there is a default flow configured in the active [**Brand**](../../../../sys-mgmt/brands/index.md). If no default is configured there, authentik will go through all flows with the matching designation, sorted by `slug`, evaluate policies bound directly to the flows, and pick the first flow whose policies allow access.
>>>>>>> e056dbdad (website/docs, integrations: fix language (#20338))

import DefaultFlowList from "../../flow/flow_list/\_defaultflowlist.mdx";

<DefaultFlowList />
