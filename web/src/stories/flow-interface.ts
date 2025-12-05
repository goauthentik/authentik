import { FlowExecutor } from "#flow/FlowExecutor";
import { SubmitOptions } from "#flow/stages/base";

import { FlowChallengeResponseRequest } from "@goauthentik/api";

import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-storybook-interface-flow")
export class StoryFlowInterface extends FlowExecutor {
    public override firstUpdated() {
        return Promise.resolve();
    }

    submit = async (
        payload?: FlowChallengeResponseRequest,
        options?: SubmitOptions,
    ): Promise<boolean> => {
        return true;
    };

    async renderChallenge(): Promise<TemplateResult> {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface-flow": StoryFlowInterface;
    }
}
