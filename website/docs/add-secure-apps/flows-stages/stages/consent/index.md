---
title: Consent stage
---

A Consent stage, if needed, is typically added to an authorization flow (either the `defauly-authorization-flow` or a [custom authorization flow](../../flow/index.md#create-a-custom-flow)). The Consent stage is used to configure the authorization server (authentik) to prompt the user for consent to share data such as user id or other non-credential type information with the relying party (RP), the application the user is logging in to.

## Example use case

This stage can be used to leverage an external OAuth source, and allow users logging into to agree that authentik can provide user data to the application you are logging in to.

## Considerations

TODO

## Consent stage workflow

insert mermaid diagram here

### Consent stage modes

The Consent stage has three configurable modes:

1. **Always require consent**: the user is prompted to give consent by clicking **Continue**.
2. **Consent given last indefinitely**: this mode stores the fact that the user previously clicked **Continue**, and creates a Consent object with a link to the user and to the application, and stores which data (but not actual value).
3. **Consent expires**: means you have to click **Continue** anytime after the expiry date that you define in the stage in the **Consent expires in....** field.

## Create and configure a Consent stage

The workflow for creating and configuring a Consent stage involves first creating the stage, creating an [Expression policy](../../../../customize/policies/expression.mdx) with the text that you want to display on the Consent prompt, and then finally bind the policy to a stage within an authorization flow.

### 1. Create a Consent stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages** and click **Create**.
3. On the **New stage** wizard select **Consent Stage** and then click **Next**.
4. Provide the following configuration settings:
    - **Name**:
    - **Stage-specific settings**:
        - **Mode**: Select the appropriate [mode](#consent-stage-modes) to use with this stage.
5. Click **Update** to save the new stage.

:::info Deciding which flow to use
Note that by default, the `default-provider-authorization-explicit-consent` flow already has a Cinsent stage added to it. However if you decide to create a custom authorization flow, you will need to [bind your Consent stage](../../../flows-stages/stages/index.md#bind-a-stage-to-a-flow) to your custom authorization flow.
:::

### 4. Bind the Cinsent stage to the authorization flow

The next step is to bind the new stage to the flow in which it will be used.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows** > **Policies** and click **Create**.
3. On the **New policy** wizard select **Expression Policy** and then click **Next**.
4. Provide the following configuration settings:
    - **Name**:

### 3. Create an Expression policy

To implement the Consent stage and have it appears to users who are logging in, you need to create an Expression policy to bind to the stage. It is in the Expression policy that you can customoze the text that appears on the consent prompt.

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

### 4. Bind the policy to the Consent stage

The last step is to bind the policy to the Consent stage, _within_ the authorization flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows** and in the list, click on the name of the authorization flow you want to use. Typically, the default authorization flow

(go to the Flow, go to Stage bindings tab, click on carot beside the stage to expand it, then bind the policy there. (Note to users about the policy is bound to the stage WITHIN this flow... not to the Stage as a whole!!))

OLD NOTES

So an end-user could delete a consent, which is same as it expires.

- in a custom flow you could add a consent stage as a key in a policy
- Default when you do the above (no app is linked no auth is processed) the default mode is Always required. ”also side use case.. OAuth can tell the IdP to re-authorize… our system auto-creates a Consent stage and add it to memory to the authz flow… only if there isn;t already one…
- OIDC has a value called consent
