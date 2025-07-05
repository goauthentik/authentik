import { SubmitOptions } from "#flow/stages/base";
import { FlowExecutor } from "@goauthentik/flow/FlowExecutor";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { FlowChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-storybook-interface-flow")
export class StoryFlowInterface extends FlowExecutor {
    async firstUpdated() {}

    async submit(
        payload?: FlowChallengeResponseRequest,
        options?: SubmitOptions,
    ): Promise<boolean> {
        return true;
    }

    async renderChallenge(): Promise<TemplateResult> {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface-flow": StoryFlowInterface;
    }
}
