---
title: Consent stage
---

The Consent stage is added to a flow to configure the authorization server (authentik) to prompt the user for consent to share data such as User ID or other non-credential type information with the relying party (RP), the application the user is logging in to.

A Consent stage is typically added to an [authorization flow](../../flow/index.md#create-a-custom-flow).

:::info Default authorization flow with a Consent stage
Note that by default, the `default-provider-authorization-explicit-consent` flow already has a Consent stage with a bound policy added to it. If you use this default flow, you do not need to take any of the below steps; the default authorization with explicit consent flow is ready for use.
:::

## Example use case

This stage is most commonly used  an provider, and prompt users to agree that authentik can provide user data to the application that the user is logging in to. This sharing of user data can facilitate tasks in the application; for example, providing an avatar, user name, or email address for the application to immediately use.

## Consent stage modes

The Consent stage has three configurable modes:

1. **Always require consent**: the user is prompted every time that they log in to give consent by clicking **Continue**.
2. **Consent given lasts indefinitely**: this mode stores the fact that the user previously clicked **Continue**, and creates a Consent object with a link to the user and to the application, and stores which data (but not actual value).
3. **Consent expires**: means you have to click **Continue** any time after the expiry date defined in the stage in the field **Consent expires in....**.

## Create and configure a Consent stage

The workflow for creating and configuring a Consent stage involves first creating the stage and binding it to an authorization flow, then creating an [Expression policy](../../../../customize/policies/expression.mdx) (with the text that you want to display on the Consent prompt), and as a final step [binding](../../../../customize/policies/working_with_policies.md#bind-a-policy-to-a-stage-binding) the policy to the Consent stage in the authorization flow.

### 1. Create a Consent stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages** and click **Create**.
3. On the **New stage** wizard select **Consent Stage** and then click **Next**.
4. Provide the following configuration settings:
    - **Name**:
    - **Stage-specific settings**:
        - **Mode**: Select the appropriate [mode](#consent-stage-modes) to use with this stage.
5. Click **Update** to save the new stage.

### 2. Bind the Consent stage to an authorization flow

To include the Consent stage in the flow, follow [these directions](../../stages/index.md#bind-a-stage-to-a-flow).

### 3. Create an Expression policy

To implement the Consent stage and have it appear to users who are logging in, you need to create an Expression policy and then bind it to the stage. It is in the Expression policy that you can customize the text that appears on the consent prompt.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies** and click **Create**.
3. On the **New policy** wizard select **Expression Policy** and then click **Next**.
4. Provide the following configuration settings:
    - **Name**:
    - **Policy-specific settings**:
        - **Expression**: use the following syntax to customize the wording on the stage:
        ```
        context['flow_plan'].context['consent_header'] = 'Are you OK with your IdP provider sharing your user identification data with the application? '
        return True
        ```
5. Click **Finish** to save the policy.

### 4. Bind the policy to the Consent stage in the authorization flow

The last step is to bind the policy that you just created in Step 3 to the Consent stage, _within_ the authorization flow.

:::info Important note about policy binding
You need to bind the policy to the stage within this flow, not to the Stage as a whole, so go first to the flow where you added the Consent stage.
:::

1. Log in to authentik as an administrator, open the authentik Admin interface, and navigate to **Flows** .
2. In the list of flows, click on the name of the authorization flow that you want to use.
3. On the **Flow overview** tab, confirm that the flow contains a Consent stage.
4. Click the **Stage Bindings** tab.
5. Click the caret (>) beside the Consent stage to which you want to bind the policy, and expand the stage details.
6. Click **Bind existing Policy / Group / User**.
7. In the **Create Binding** dialog, click **Policy** and then select the Expression policy that you created in Step 2 above.
:::
8. Click **Create** to save the binding.
