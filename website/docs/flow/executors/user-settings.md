---
title: User settings
---

:::info
Requires authentik 2022.3
:::

The user interface (`/if/user/`) embeds a downsized flow executor to allow the user to configure their profile using custom stages and prompts.

This executor only supports [**prompt**](../stages/prompt/) stages. If the configured flow contains another stage, a button will be shown to open the default executor.
Because the stages in a flow can change during it execution, this executor will redirect the user to the default interface _if_ a non-supported stage is returned.

To configure which flow is used for this, configure it in the tenant settings.
