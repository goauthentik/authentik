---
title: Default flows
---

When you create a new provider, you can select certain default flows that will be used with the provider and its associated application. For example, you can select the `default-authentication-flow` (Welcome to authentik!) flow to be presented to all users logging in and authenticating with this provider and application. (You can of course also [create a custom flow](../index.md#create-a-custom-flow))

If no default flow is selected when the provider is created, to determine which flow should be used authentik will first check if there is a default flow configured in the active [**Brand**](../../../../customize/brands.md). If no default is configured there, then the policies in all flows with the matching designation are checked, and the first flow with matching policies sorted by `slug` will be used.

import Defaultflowlist from "../../flow/flow_list/\_defaultflowlist.mdx";

<Defaultflowlist />

##
