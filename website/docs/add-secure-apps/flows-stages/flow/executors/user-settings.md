---
title: User settings
---

The user interface (/if/user/) uses a specialized flow executor to allow individual users to customize their profile. A user's profile consists of key/value fields, so this executor only supports Prompt or User Write stages. If the configured flow contains another stage, a button will be shown to open the default executor.

Because the stages in a flow can change during its execution, be awre that configuring this executor to use any stage type other than Prompt or User Write will automatically trigger a redirect to the standard executor.

An admin can customize which fields can be changed by the user by updating the default-user-settings-flow, or copying it to create a new flow with a Prompt Stage and a User Write Stage. Different variants of your flow can be applied to different [Brands](../../../../customize/brands.md) on the same authentik instance.
