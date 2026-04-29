---
title: Consent stage
---

The Consent stage is added to a flow to prompt the user for consent to share data such as User ID or other non-credential type information with the relying party (RP), the application the user is logging in to.

A Consent stage is typically added to an [authorization flow](../../flow/index.md#create-a-flow), but can be added to any flow.

:::info Default authorization flow with a Consent stage
Note that by default, the `default-provider-authorization-explicit-consent` flow already has a Consent stage bound to it. If you use this default flow, you do not need to take any of the below steps; the `default-provider-authorization-explicit-consent` flow is ready for use.
:::

## Example use case

This stage is to prompt users when they access an application to agree that authentik can provide user data to the application that the user is logging in to. This sharing of user data can facilitate tasks in the application; for example, providing an avatar, user name, or email address for the application to immediately use.

## Consent stage modes

The Consent stage has three configurable modes:

1. **Always require consent**: the user is prompted every time that they log in to give consent by clicking **Continue**.
2. **Consent given lasts indefinitely**: this mode stores the fact that the user previously clicked **Continue**, and creates a Consent object with a link to the user and to the application, and stores which permissions were consented to.
3. **Consent expires**: similar to **Consent given lasts indefinitely**, except the consent expires on the date defined in the stage in the field **Consent expires in**.

## Create and configure a Consent stage

If you want to add the consent stage to a flow other than the `default-provider-authorization-explicit-consent` flow (which already has a Consent stage bound to it), use the following steps.

The basic workflow for creating and configuring a Consent stage involves creating the stage and then binding it to an authorization flow.

Optionally, if you also want to customize the exact wording that appears on the consent prompt, you can create an [Expression policy](../../../../customize/policies/types/expression/index.mdx) with the text that you want to display on the Consent prompt, and then [bind](../../../../customize/policies/working_with_policies.md#bind-a-policy-to-a-stage-binding) the policy to the Consent stage binding in the authorization flow.

### 1. Create a Consent stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages** and click **New Stage**.
3. On the **New stage** wizard select **Consent Stage** and then click **Next**.
4. Provide the following configuration settings:
    - **Name**:
    - **Stage-specific settings**:
        - **Mode**: Select the appropriate [mode](#consent-stage-modes) to use with this stage.
5. Click **Create Stage** to save the new stage.

### 2. Bind the Consent stage to an authorization flow

To include the Consent stage in the flow, follow [these directions](../../stages/index.md#bind-a-stage-to-a-flow).

### 3. Create an Expression policy (_optional_)

If you want to customize the text that appears on the consent prompt, you can create an Expression policy with the exact wording you want, and then bind it to the Consent stage in the flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies** and click **New Policy**.
3. On the **New policy** wizard select **Expression Policy** and then click **Next**.
4. Provide the following configuration settings:
    - **Name**:
    - **Policy-specific settings**:
        - **Expression**: use the following syntax to customize the wording on the stage:
        ````
        context['flow_plan'].context['consent_header'] = "Are you OK with your IdP provider sharing your user identification data with the application?"
        return True
        ```python
        ````
5. Click **Create Policy** to save the policy.

### 4. Bind the policy to the Consent stage in the authorization flow (_optional_)

The last step is to bind the policy that you just created in Step 3 to the Consent stage binding, _within_ the authorization flow.

:::info Important note about policy binding
You need to bind the policy to the stage within this flow, so go first to the flow where you added the Consent stage.
:::

1. Log in to authentik as an administrator, open the authentik Admin interface, and navigate to **Flows and Stages > Flows**.
2. In the list of flows, click on the name of the authorization flow that you want to use.
3. On the **Flow overview** tab, confirm that the flow contains a Consent stage.
4. Click the **Stage Bindings** tab.
5. Click the caret (>) beside the Consent stage to which you want to bind the policy, and expand the stage details.
6. Click **Bind existing Policy/Group/User**.
7. In the **Create Binding** dialog, click **Policy** and then select the Expression policy that you created above.
8. Click **Create Policy Binding** to save the binding.
